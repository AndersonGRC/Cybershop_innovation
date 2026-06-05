"""CRUD de tenants + acciones sobre sus API keys."""

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort, session
)

from auth import login_required
import tenant_service
import api_key_service
import client_config_service as ccs
import module_service as ms
import integrations_service as ints
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

    # Integraciones (env por instancia; no requiere la BD del cliente)
    integraciones = ints.get_integrations(tenant['slug'])

    # Runtime (puerto, dominio, estado de instancia) + preview del proxy
    proxy_preview = None
    try:
        import provisioning_service as prov
        from config import Config
        runtime = prov.get_runtime(tenant_id)
        if runtime and runtime.get('port'):
            import proxy_service
            dom = prov.domain_for(runtime['subdomain'])
            proxy_preview = proxy_service.preview_block(dom, runtime['port'], is_subdomain=True)
            if runtime.get('custom_domain'):
                proxy_preview += "\n" + proxy_service.preview_block(runtime['custom_domain'], runtime['port'], is_subdomain=False)
    except Exception:  # noqa: BLE001
        runtime = None

    from config import Config as _Cfg
    return render_template(
        'tenant_detail.html', tenant=tenant, keys=keys,
        cfg=cfg, secs=secs, mods=mods, site_error=site_error,
        integraciones=integraciones, runtime=runtime,
        proxy_preview=proxy_preview, server_ip=_Cfg.SERVER_IP,
        proxy_backend=_Cfg.PROXY_BACKEND,
        empresa_fields=ccs.EMPRESA_FIELDS, color_fields=ccs.COLOR_FIELDS,
        section_fields=ccs.SECTION_FIELDS, plans=ms.PLANS,
    )


@bp.route('/<int:tenant_id>/integraciones', methods=['POST'])
@login_required
def integraciones_save(tenant_id):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    try:
        ints.save_integrations(tenant['slug'], request.form)
        flash('Integraciones guardadas. Se aplican al reiniciar la instancia del cliente.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error guardando integraciones: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#integraciones')


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
    import lifecycle_service as lc
    try:
        if tenant['estado'] == 'activo':
            lc.suspend(tenant_id)
            flash('Cliente suspendido: instancia apagada (no permite ingreso) y API keys desactivadas.', 'success')
        else:
            lc.reactivate(tenant_id)
            flash('Cliente reactivado. Revisá que la instancia esté arriba y reactivá las API keys necesarias.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error cambiando estado: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')


@bp.route('/<int:tenant_id>/instancia', methods=['POST'])
@login_required
def instancia_accion(tenant_id):
    """Acciones sobre la instancia/BD del cliente: reiniciar, migrar BD, reaprovisionar."""
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    accion = (request.form.get('accion') or '').strip()
    try:
        import provisioning_service as prov
        if accion == 'restart':
            prov.restart_service(tenant['slug'])
            flash('Instancia reiniciada (en el servidor). En dev no aplica.', 'success')
        elif accion == 'reprovision':
            r = prov.provision(tenant_id, tenant['slug'], tenant['db_name'], subdomain=tenant['slug'])
            flash(f"Reaprovisionado: puerto {r['port']}, dominio {r['domain']}.", 'success')
        elif accion == 'migrate':
            import tenant_migrations as tm
            applied = tm.migrate_db(tenant['db_name'])
            flash(f"Migración de BD: {len(applied)} aplicada(s)." if applied else "BD al día (nada que migrar).", 'success')
        else:
            flash('Acción no reconocida.', 'warning')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error en la acción de instancia: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')


@bp.route('/<int:tenant_id>/dominio', methods=['POST'])
@login_required
def dominio_save(tenant_id):
    """Configura subdominio y dominio propio del cliente (aprovisiona si falta)."""
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    if not tenant.get('db_name'):
        flash('El cliente no tiene BD; no se puede aprovisionar el dominio.', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')
    subdominio = (request.form.get('subdominio') or tenant['slug']).strip().lower()
    dominio_propio = (request.form.get('dominio_propio') or '').strip().lower() or None
    try:
        import provisioning_service as prov
        import proxy_service
        r = prov.provision(tenant_id, tenant['slug'], tenant['db_name'],
                           subdomain=subdominio, custom_domain=dominio_propio)
        flash(f"Dominio configurado: {r['domain']}"
              + (f" + {dominio_propio}" if dominio_propio else "")
              + f" → puerto {r['port']}.", 'success')
    except proxy_service.DomainError as exc:
        flash(str(exc), 'error')
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if 'unique' in msg or 'duplicate' in msg:
            flash('Ese subdominio o dominio propio ya está usado por otro cliente. Elige otro.', 'error')
        else:
            flash(f'Error configurando dominio: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')


@bp.route('/<int:tenant_id>/destroy', methods=['POST'])
@login_required
def destroy(tenant_id):
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    import lifecycle_service as lc
    mode = (request.form.get('mode') or 'soft').strip()
    confirm = (request.form.get('confirm_slug') or '').strip()
    if confirm != tenant['slug']:
        flash('Confirmación inválida: escribe el slug exacto del cliente.', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')
    try:
        if mode == 'hard':
            backup = lc.destroy_hard(tenant_id)
            flash(f'Cliente ELIMINADO (hard). Backup en {backup}. La BD fue borrada.', 'warning')
        else:
            backup = lc.destroy_soft(tenant_id)
            flash(f'Cliente cancelado (soft). Backup en {backup}. La BD se conservó.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error destruyendo cliente: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')


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
