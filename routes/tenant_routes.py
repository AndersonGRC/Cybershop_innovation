"""CRUD de tenants + acciones sobre sus API keys."""

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort, session
)

from auth import login_required
import tenant_service
import api_key_service
import client_config_service as ccs
import module_service as ms
from tenant_service import TenantCreationError


bp = Blueprint('tenants', __name__, url_prefix='/tenants')


# ── Lista ────────────────────────────────────────────────────────

@bp.route('/')
@login_required
def lista():
    search = request.args.get('q', '').strip()
    tenants = tenant_service.list_tenants(search=search)
    return render_template('tenant_list.html', tenants=tenants, search=search)


# ── Crear ────────────────────────────────────────────────────────

@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        slug = request.form.get('slug', '')
        nombre = request.form.get('nombre', '')
        try:
            result = tenant_service.create_tenant(slug=slug, nombre=nombre)
        except TenantCreationError as exc:
            flash(str(exc), 'error')
            return render_template(
                'tenant_new.html',
                form={'slug': slug, 'nombre': nombre},
            )

        # Stash credenciales en sesión flash (UNA SOLA VEZ)
        session['_created_tenant'] = result
        return redirect(url_for('tenants.created', tenant_id=result['tenant_id']))

    return render_template('tenant_new.html', form={'slug': '', 'nombre': ''})


@bp.route('/<int:tenant_id>/created')
@login_required
def created(tenant_id):
    """Muestra api_key + client_code recién creados UNA sola vez.

    Se obtiene de la sesión flash; al renderizar se borra para que
    no sea recuperable refrescando la página."""
    info = session.pop('_created_tenant', None)
    if not info or info.get('tenant_id') != tenant_id:
        flash(
            'Las credenciales solo se muestran una vez al crear el tenant. '
            'Si necesitas otra, generá una nueva key desde el detalle.',
            'warning'
        )
        return redirect(url_for('tenants.detail', tenant_id=tenant_id))
    return render_template('tenant_created.html', info=info)


# ── Detalle ──────────────────────────────────────────────────────

@bp.route('/<int:tenant_id>')
@login_required
def detail(tenant_id):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    keys = api_key_service.list_keys(tenant_id)

    # Config/secciones/módulos del cliente (requiere su BD)
    cfg = secs = mods = None
    site_error = None
    if tenant.get('db_name'):
        try:
            cfg = ccs.get_config(tenant_id)
            secs = ccs.get_sections(tenant_id)
            mods = ms.get_modules(tenant_id)
        except Exception as exc:  # noqa: BLE001
            site_error = str(exc)

    return render_template(
        'tenant_detail.html', tenant=tenant, keys=keys,
        cfg=cfg, secs=secs, mods=mods, site_error=site_error,
        empresa_fields=ccs.EMPRESA_FIELDS, color_fields=ccs.COLOR_FIELDS,
        section_fields=ccs.SECTION_FIELDS, plans=ms.PLANS,
    )


@bp.route('/<int:tenant_id>/config', methods=['POST'])
@login_required
def config_save(tenant_id):
    try:
        ccs.save_config(tenant_id, request.form)
        flash('Configuración del sitio actualizada.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error guardando configuración: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#config')


@bp.route('/<int:tenant_id>/secciones', methods=['POST'])
@login_required
def secciones_save(tenant_id):
    try:
        ccs.save_sections(tenant_id, request.form)
        flash('Secciones del sitio actualizadas.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error guardando secciones: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#secciones')


@bp.route('/<int:tenant_id>/modulos', methods=['POST'])
@login_required
def modulos_save(tenant_id):
    try:
        plan = (request.form.get('plan') or '').strip()
        if plan:
            ms.apply_plan(tenant_id, plan)
            flash(f"Plan '{plan}' aplicado a los módulos del cliente.", 'success')
        else:
            ms.save_modules(tenant_id, request.form.getlist('modulo'))
            flash('Módulos del cliente actualizados.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error guardando módulos: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#modulos')


@bp.route('/<int:tenant_id>/toggle', methods=['POST'])
@login_required
def toggle(tenant_id):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    nuevo_estado = 'suspendido' if tenant['estado'] == 'activo' else 'activo'
    tenant_service.set_estado(tenant_id, nuevo_estado)
    if nuevo_estado == 'suspendido':
        flash('Tenant suspendido. Todas sus API keys quedaron desactivadas.', 'success')
    else:
        flash(
            'Tenant reactivado. Recordá activar manualmente las API keys que quieras volver a usar.',
            'success'
        )
    return redirect(url_for('tenants.detail', tenant_id=tenant_id))


# ── API keys del tenant ──────────────────────────────────────────

@bp.route('/<int:tenant_id>/keys/nueva', methods=['POST'])
@login_required
def key_nueva(tenant_id):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    label = request.form.get('label', '').strip() or 'API key adicional'
    try:
        result = api_key_service.issue_key(tenant_id, label=label)
    except Exception as exc:  # noqa: BLE001
        flash(f'Error emitiendo key: {exc}', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id))

    # Reusamos la vista created para mostrar la nueva key una sola vez
    session['_created_tenant'] = {
        'tenant_id':   tenant_id,
        'slug':        tenant['slug'],
        'nombre':      tenant['nombre'],
        'db_name':     tenant['db_name'],
        'api_key':     result['api_key'],
        'client_code': result['client_code'],
        'key_prefix':  result['key_prefix'],
        'key_id':      result['id'],
    }
    return redirect(url_for('tenants.created', tenant_id=tenant_id))


@bp.route('/<int:tenant_id>/keys/<int:key_id>/rotate', methods=['POST'])
@login_required
def key_rotate(tenant_id, key_id):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    try:
        result = api_key_service.rotate(key_id)
    except Exception as exc:  # noqa: BLE001
        flash(f'Error rotando key: {exc}', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id))

    session['_created_tenant'] = {
        'tenant_id':   tenant_id,
        'slug':        tenant['slug'],
        'nombre':      tenant['nombre'],
        'db_name':     tenant['db_name'],
        'api_key':     result['api_key'],
        'client_code': result['client_code'],
        'key_prefix':  result['key_prefix'],
        'key_id':      result['id'],
    }
    flash('Key vieja desactivada y nueva emitida.', 'success')
    return redirect(url_for('tenants.created', tenant_id=tenant_id))


@bp.route('/<int:tenant_id>/keys/<int:key_id>/suspend', methods=['POST'])
@login_required
def key_suspend(tenant_id, key_id):
    try:
        api_key_service.set_active(key_id, False)
        flash('Key desactivada.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id))


@bp.route('/<int:tenant_id>/keys/<int:key_id>/activate', methods=['POST'])
@login_required
def key_activate(tenant_id, key_id):
    try:
        api_key_service.set_active(key_id, True)
        flash('Key activada.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id))
