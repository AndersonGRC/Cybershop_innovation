"""Pruebas por limpiar: tiendas de prueba gratis que vencieron sin pagar y
ocupan recursos (instancia, BD, dirección). Se eliminan en bloque con el mismo
camino del botón «Eliminar + backup (DROP BD)» de cada cliente.

Seguridad:
- El servidor vuelve a calcular la lista antes de eliminar: un id que no sea
  una prueba vencida sin pagar se ignora (una tienda que pagó nunca entra).
- Confirmación escribiendo ELIMINAR y máximo 10 por vez (cada una saca backup).
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from auth import current_admin, login_required
import billing_service
import lifecycle_service as lc
import tenant_service

bp = Blueprint('pruebas', __name__, url_prefix='/pruebas')

DIAS_GRACIA = 7
MAX_POR_VEZ = 10


def _por():
    admin = current_admin()
    return admin['email'] if admin else 'maestro'


def _candidatas():
    filas = billing_service.pruebas_por_limpiar(DIAS_GRACIA)
    salida = []
    for f in filas:
        t = tenant_service.get_tenant(f['tenant_id'])
        if not t:
            continue
        if t['estado'] == 'cancelado' and not t.get('db_name'):
            continue
        f['slug'] = t['slug']
        f['estado_cliente'] = t['estado']
        salida.append(f)
    return salida


@bp.route('/')
@login_required
def lista():
    candidatas = _candidatas()
    backups = lc.backups_pruebas_vencidos()
    return render_template('pruebas_limpiar.html', candidatas=candidatas, dias_gracia=DIAS_GRACIA,
                           max_por_vez=MAX_POR_VEZ, backups=backups,
                           backups_mb=round(sum(b['bytes'] for b in backups) / 1048576, 1),
                           retencion=lc.RETENCION_BACKUPS_PRUEBAS_DIAS)


@bp.route('/eliminar', methods=['POST'])
@login_required
def eliminar():
    if (request.form.get('confirmacion') or '').strip().upper() != 'ELIMINAR':
        flash('Para eliminar escribe ELIMINAR en la confirmación.', 'error')
        return redirect(url_for('pruebas.lista'))
    pedidas = {int(x) for x in request.form.getlist('tenant_id') if str(x).isdigit()}
    permitidas = {c['tenant_id']: c for c in _candidatas()}
    elegidas = [tid for tid in pedidas if tid in permitidas][:MAX_POR_VEZ]
    ignoradas = len(pedidas) - len([t for t in pedidas if t in permitidas])
    if not elegidas:
        flash('No hay pruebas válidas seleccionadas.', 'warning')
        return redirect(url_for('pruebas.lista'))
    ok, errores = [], []
    for tid in elegidas:
        try:
            lc.destroy_hard(tid, actor=_por())
            ok.append(permitidas[tid]['slug'])
        except Exception as exc:  # noqa: BLE001
            errores.append(f"{permitidas[tid]['slug']}: {exc}")
    if ok:
        flash(f'Eliminadas {len(ok)} prueba(s) con backup: {", ".join(ok)}.', 'success')
    if errores:
        flash('No se pudieron eliminar: ' + ' | '.join(errores), 'error')
    if ignoradas:
        flash(f'{ignoradas} selección(es) ignorada(s): ya no son pruebas vencidas sin pagar.', 'warning')
    return redirect(url_for('pruebas.lista'))


@bp.route('/backups/purgar', methods=['POST'])
@login_required
def purgar_backups():
    archivos, total = lc.purgar_backups_pruebas(actor=_por())
    flash(f'Se borraron {archivos} copia(s) de pruebas eliminadas hace más de '
          f'{lc.RETENCION_BACKUPS_PRUEBAS_DIAS} días ({round(total / 1048576, 1)} MB liberados).', 'success')
    return redirect(url_for('pruebas.lista'))
