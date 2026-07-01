"""CRUD de tenants + acciones sobre sus API keys."""

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort, session,
    jsonify,
)

from auth import login_required
import tenant_service
import api_key_service
import client_config_service as ccs
import module_service as ms
import integrations_service as ints
import billing_service
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
        admin_email = request.form.get('admin_email', '')
        admin_nombre = request.form.get('admin_nombre', '')
        plan = request.form.get('plan', 'estandar')
        telefono = request.form.get('empresa_telefono', '')
        whatsapp = request.form.get('empresa_whatsapp', '')
        form = {'slug': slug, 'nombre': nombre, 'admin_email': admin_email,
                'admin_nombre': admin_nombre, 'plan': plan,
                'empresa_telefono': telefono, 'empresa_whatsapp': whatsapp}
        try:
            result = tenant_service.create_tenant(
                slug=slug, nombre=nombre, admin_email=admin_email,
                admin_nombre=admin_nombre, plan=plan,
            )
        except TenantCreationError as exc:
            flash(str(exc), 'error')
            return render_template('tenant_new.html', form=form, plans=ms.PLANS)

        # Datos de contacto opcionales en la BD del cliente (no aborta si falla).
        try:
            ccs.set_values(result['tenant_id'], {
                'empresa_telefono': telefono,
                'empresa_whatsapp': whatsapp,
            })
        except Exception as exc:  # noqa: BLE001
            flash(f'Tenant creado, pero no se pudieron guardar los datos de contacto: {exc}', 'warning')

        # Avisos no críticos del aprovisionamiento (módulos/instancia pendientes).
        for w in (result.get('warnings') or []):
            flash(f'Aviso: {w}', 'warning')

        # Stash credenciales en sesión flash (UNA SOLA VEZ)
        session['_created_tenant'] = result
        return redirect(url_for('tenants.created', tenant_id=result['tenant_id']))

    return render_template(
        'tenant_new.html',
        form={'slug': '', 'nombre': '', 'admin_email': '', 'admin_nombre': '',
              'plan': 'estandar', 'empresa_telefono': '', 'empresa_whatsapp': ''},
        plans=ms.PLANS,
    )


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


# ── Acceso del cliente (usuario admin de su panel) ───────────────

@bp.route('/<int:tenant_id>/admin/reset-password', methods=['POST'])
@login_required
def admin_reset_password(tenant_id):
    """Regenera la contraseña del administrador del cliente y la muestra 1 vez."""
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    try:
        result = tenant_service.reset_admin_password(tenant_id)
    except Exception as exc:  # noqa: BLE001
        flash(f'No se pudo regenerar la contraseña: {exc}', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')

    # Stash en sesión flash: se muestra UNA sola vez (igual que las API keys).
    session['_reset_admin_pw'] = {
        'tenant_id':      tenant_id,
        'slug':           tenant['slug'],
        'nombre':         tenant['nombre'],
        'admin_email':    result['admin_email'],
        'admin_password': result['admin_password'],
    }
    return redirect(url_for('tenants.admin_password_shown', tenant_id=tenant_id))


@bp.route('/<int:tenant_id>/admin/password')
@login_required
def admin_password_shown(tenant_id):
    """Muestra la contraseña recién regenerada UNA sola vez (se borra al verla)."""
    info = session.pop('_reset_admin_pw', None)
    if not info or info.get('tenant_id') != tenant_id:
        flash(
            'La contraseña regenerada solo se muestra una vez. Si la perdiste, '
            'vuelve a regenerarla desde la pestaña Técnico del tenant.',
            'warning',
        )
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#tecnico')
    return render_template('admin_password_reset.html', info=info)


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

    # Facturación electrónica: estado local (sin red) + prefill desde BILLING_*
    # dian_service es trabajo en progreso: si aún no existe, el panel funciona
    # igual y la tarjeta DIAN simplemente no se muestra.
    dian = None
    try:
        import dian_service as ds
        dian = ds.get_status(tenant['slug'])
        _env = ints.read_env(tenant['slug'])
        dian['prefill'] = {
        'nit': _env.get('BILLING_ID', ''),
            'razon_social': _env.get('BILLING_NOMBRE', '') or tenant.get('nombre', ''),
        }
    except Exception:
        dian = None

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

    # Cobros / mora del cliente
    try:
        billing = billing_service.get_billing(tenant_id)
    except Exception:  # noqa: BLE001
        billing = None

    from config import Config as _Cfg
    return render_template(
        'tenant_detail.html', tenant=tenant, keys=keys,
        cfg=cfg, secs=secs, mods=mods, site_error=site_error,
        integraciones=integraciones, dian=dian, runtime=runtime,
        proxy_preview=proxy_preview, server_ip=_Cfg.SERVER_IP,
        proxy_backend=_Cfg.PROXY_BACKEND,
        primary_slug=_Cfg.PRIMARY_TENANT_SLUG,
        site_fields=__import__('tenant_site_fields').SITE_FIELDS,
        site_groups=__import__('tenant_site_fields').SITE_GROUPS,
        section_fields=ccs.SECTION_FIELDS, plans=ms.PLANS,
        billing=billing,
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


@bp.route('/<int:tenant_id>/ai/models')
@login_required
def ai_models(tenant_id):
    """AJAX: consulta EN VIVO los modelos del servidor de IA y los cachea.
    Lo usa el boton "Actualizar modelos" del panel de Integraciones. No bloquea
    la carga de la pagina (esto corre solo cuando el operador lo pide)."""
    from config import Config as _Cfg
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        return jsonify({'models': [], 'online': False, 'error': 'tenant no encontrado'}), 404
    base = (request.args.get('base_url') or '').strip()
    if not base:
        base = ints.read_env(tenant['slug']).get('AI_BASE_URL', '')
    base = base or _Cfg.AI_DEFAULT_BASE_URL
    models = ints.refresh_ai_models(base)
    return jsonify({'models': models, 'online': bool(models), 'base_url': base})


# ── Cobros / mora ────────────────────────────────────────────────

def _por():
    return session.get('admin_email') or session.get('admin') or 'maestro'


@bp.route('/<int:tenant_id>/billing/config', methods=['POST'])
@login_required
def billing_config(tenant_id):
    if not tenant_service.get_tenant(tenant_id):
        abort(404)
    try:
        billing_service.set_config(
            tenant_id,
            monto_mensual=request.form.get('monto_mensual'),
            proxima_fecha=request.form.get('proxima_fecha'),
            auto_suspender=('auto_suspender' in request.form),
            notas=request.form.get('notas'),
        )
        flash('Configuración de cobro guardada.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error guardando cobro: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#cobros')


@bp.route('/<int:tenant_id>/billing/pago', methods=['POST'])
@login_required
def billing_pago(tenant_id):
    if not tenant_service.get_tenant(tenant_id):
        abort(404)
    try:
        nueva = billing_service.registrar_pago(
            tenant_id,
            monto=request.form.get('monto'),
            fecha=request.form.get('fecha'),
            metodo=request.form.get('metodo'),
            nota=request.form.get('nota'),
            registrado_por=_por(),
        )
        flash(f'Pago registrado. Próximo vencimiento: {nueva}.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error registrando pago: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#cobros')


@bp.route('/<int:tenant_id>/billing/plazo', methods=['POST'])
@login_required
def billing_plazo(tenant_id):
    if not tenant_service.get_tenant(tenant_id):
        abort(404)
    try:
        destino = billing_service.extender_plazo(
            tenant_id,
            dias=request.form.get('dias') or None,
            nueva_fecha=request.form.get('nueva_fecha') or None,
        )
        flash(f'Plazo extendido. Nuevo vencimiento: {destino}.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error extendiendo plazo: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#cobros')


@bp.route('/billing/revisar-morosos', methods=['POST'])
@login_required
def billing_revisar_morosos():
    try:
        suspendidos = billing_service.revisar_y_suspender(por='manual')
        if suspendidos:
            flash('Suspendidos por mora (+%d días): %s' % (
                billing_service.MORA_DIAS_SUSPENSION,
                ', '.join('%s (#%d)' % (m['slug'], m['id']) for m in suspendidos)), 'warning')
        else:
            flash('No hay morosos elegibles para suspender.', 'info')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error revisando morosos: {exc}', 'error')
    return redirect(url_for('tenants.lista'))


@bp.route('/<int:tenant_id>/config', methods=['POST'])
@login_required
def config_save(tenant_id):
    try:
        ccs.save_config(tenant_id, request.form)
        flash('Configuración del sitio actualizada.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error guardando configuración: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#config')


@bp.route('/<int:tenant_id>/logo', methods=['POST'])
@login_required
def logo_upload(tenant_id):
    """Sube/cambia el logo del sitio público (antes del login) del cliente."""
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    f = request.files.get('logo')
    if not f or not f.filename:
        flash('Selecciona un archivo de imagen para el logo.', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#config')
    try:
        ccs.save_logo(tenant_id, f)
        flash('Logo del sitio público actualizado. Refresca el sitio con Ctrl+F5 para verlo.', 'success')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error subiendo el logo: {exc}', 'error')
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
        # Degradación controlada: si Ventas/POS quedó habilitado pero PayU no
        # está configurado, avisar (el sitio oculta el pago en línea solo).
        try:
            import integrations_service as ints
            t = tenant_service.get_tenant(tenant_id)
            envv = ints.read_env(t['slug']) if t else {}
            ventas_on = ('pos' in request.form.getlist('modulo')
                         or 'orders' in request.form.getlist('modulo')
                         or (request.form.get('plan') or '').strip() != '')
            if ventas_on and not envv.get('PAYU_MERCHANT_ID'):
                flash('Ventas habilitado pero PayU NO está configurado para este cliente: '
                      'su tienda mostrará el catálogo y el carrito, pero el pago en línea '
                      'quedará oculto (solo WhatsApp) hasta llenar la pestaña Integraciones.', 'error')
            fe_on = ('facturacion_electronica' in request.form.getlist('modulo'))
            if fe_on and not envv.get('DIAN_API_KEY'):
                flash('Facturación DIAN activada pero el cliente NO tiene credenciales del '
                      'servicio: la app no podrá emitir facturas. Ve a Integraciones → '
                      'Facturación Electrónica y usa "Provisionar en servicio DIAN".', 'error')
        except Exception:
            pass
        # Reiniciar la instancia para que el cambio tome efecto al instante: el
        # app cachea los flags de módulos por proceso, sin reinicio el toggle no
        # se vería hasta el siguiente arranque. Aplica a todos los módulos.
        try:
            import provisioning_service as prov
            t = tenant_service.get_tenant(tenant_id)
            if t and prov.IS_LINUX:
                prov.restart_service(t['slug'])
        except Exception:
            pass
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


@bp.route('/<int:tenant_id>/dian/provision', methods=['POST'])
@login_required
def dian_provision(tenant_id):
    """Provisiona el tenant en FacturacionDIAN y escribe DIAN_* en su env."""
    try:
        import dian_service  # noqa: F401
    except Exception:
        flash('Función DIAN aún no disponible (dian_service en desarrollo).', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#integraciones')
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    import dian_service as ds
    try:
        r = ds.provision(
            tenant['slug'],
            nombre=tenant.get('nombre') or tenant['slug'],
            nit=request.form.get('nit', ''),
            razon_social=request.form.get('razon_social', ''),
            dv=(request.form.get('dv') or '').strip() or None,
            ambiente=(request.form.get('ambiente') or 'habilitacion').strip(),
            prefijo=request.form.get('prefijo', ''),
        )
        flash(f"Tenant DIAN creado (NIT {r['nit']}-{r['dv']}) y credenciales escritas "
              "en el env de la instancia.", 'success')
        # Reiniciar la instancia para que la app tome las credenciales nuevas
        try:
            import provisioning_service as prov
            prov.restart_service(tenant['slug'])
            flash('Instancia reiniciada: la facturación electrónica ya está operativa '
                  '(falta subir certificado y resolución en el panel DIAN).', 'success')
        except Exception:  # noqa: BLE001 — en dev local no hay systemd
            flash('Reinicia la instancia del cliente (pestaña Técnico) para aplicar '
                  'las credenciales.', 'warning')
    except ds.DianError as exc:
        flash(str(exc), 'error')
    except Exception as exc:  # noqa: BLE001
        flash(f'Error provisionando en DIAN: {exc}', 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#integraciones')


@bp.route('/<int:tenant_id>/dian/validate', methods=['POST'])
@login_required
def dian_validate(tenant_id):
    """Valida la cadena completa admin → servicio DIAN → credenciales del cliente."""
    try:
        import dian_service  # noqa: F401
    except Exception:
        flash('Función DIAN aún no disponible (dian_service en desarrollo).', 'error')
        return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#integraciones')
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        abort(404)
    import dian_service as ds
    try:
        checks = ds.validate(tenant['slug'])
        # Estado del módulo en la app del cliente (cliente_config)
        try:
            mods = ms.get_modules(tenant_id)
            fe = next((m for m in mods if m['code'] == 'facturacion_electronica'), None)
            checks.insert(0, (bool(fe and fe['is_active']),
                              "Módulo 'Facturación DIAN' activo en la app del cliente"))
        except Exception:  # noqa: BLE001 — BD del tenant caída no invalida el resto
            pass
        ok = sum(1 for passed, _ in checks if passed)
        for passed, label in checks:
            flash(('✓ ' if passed else '✗ ') + label, 'success' if passed else 'error')
        flash(f"Validación DIAN: {ok}/{len(checks)} comprobaciones OK.",
              'success' if ok == len(checks) else 'warning')
    except ds.DianError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('tenants.detail', tenant_id=tenant_id) + '#integraciones')


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
        elif accion == 'repair':
            # Limpia el unit templated fantasma del primario (crash-loop). NO toca
            # el servicio real `cybershop` que sirve el sitio principal.
            msg = prov.repair_primary_unit()
            flash(f'Reparación de instancia: {msg}.', 'success')
        elif accion == 'sync_status':
            activo = prov.service_is_active(tenant['slug'])
            prov.set_status(tenant_id, 'running' if activo else 'stopped')
            flash(f"Estado sincronizado con el servidor: instancia "
                  f"{'ACTIVA' if activo else 'detenida'}.", 'success')
        elif accion == 'reprovision':
            r = prov.provision(tenant_id, tenant['slug'], tenant['db_name'], subdomain=tenant['slug'])
            flash(f"Reaprovisionado: puerto {r['port']}, dominio {r['domain']}.", 'success')
        elif accion == 'migrate':
            import tenant_migrations as tm
            applied = tm.migrate_db(tenant['db_name'])
            flash(f"Migración de BD: {len(applied)} aplicada(s)." if applied else "BD al día (nada que migrar).", 'success')
        elif accion == 'update':
            # "Actualizar app": replica al cliente lo FUNCIONAL (después del login)
            # + seguridad/backend, SIN tocar su sitio público ni sus datos.
            #   1) TRAER el código desde GitHub con GATE de cambios públicos
            #      (deploy_code); si hay cambios públicos y no include_public → BLOQUEA;
            #   2) migrar estructura de su BD (aditivo — no toca cliente_config /
            #      public_site_settings / config_secciones, que son SUS datos);
            #   3) reiniciar su instancia para que cargue el código nuevo.
            # "Deploy completo" (include_public=1) trae también el sitio público.
            import tenant_migrations as tm
            include_public = bool(request.form.get('include_public'))
            status, msg_deploy = prov.deploy_code(include_public=include_public)
            if status == 'blocked':
                flash("No se actualizó (nada se aplicó): " + msg_deploy, 'warning')
            elif status == 'error':
                flash("Error trayendo el código: " + msg_deploy
                      + " — no se migró ni reinició.", 'error')
            else:  # 'updated' | 'uptodate' → migrar (aditivo) + reiniciar
                partes = [f"código: {msg_deploy}"]
                applied = tm.migrate_db(tenant['db_name'])
                partes.append(f"{len(applied)} migración(es) de BD" if applied else "BD ya al día")
                prov.restart_service(tenant['slug'])
                partes.append("instancia reiniciada" if prov.IS_LINUX else "reinicio omitido (dev)")
                flash("Cliente actualizado: " + "; ".join(partes)
                      + ". Su sitio público (colores, logo, secciones, datos) quedó intacto.",
                      'success')
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
        if r.get('ssl'):
            ok = 'certificado activo' in r['ssl']
            flash(r['ssl'], 'success' if ok else 'error')
            if not ok:
                flash('Si el DNS acaba de crearse, espera 1-2 min y usa "Reaprovisionar" para reintentar el SSL.', 'error')
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
