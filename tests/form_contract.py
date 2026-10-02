"""Contrato de los formularios de la ficha del cliente.

Renderiza `tenant_detail.html` con un contexto simulado (sin BD ni red) y
extrae cada formulario: a dónde envía, con qué método y qué campos manda.
Sirve para reorganizar la presentación con la garantía de que el backend
recibe exactamente lo mismo que antes.
"""

from datetime import date, datetime
from html.parser import HTMLParser


class _Formularios(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self._f = None
        self._select = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self._f = {'action': a.get('action', ''), 'method': (a.get('method') or 'get').lower(),
                       'enctype': a.get('enctype', ''), 'editables': set(), 'envia': set(), 'opciones': set()}
            self.forms.append(self._f)
            return
        f = self._f
        if f is None:
            return
        nombre = a.get('name')
        if tag == 'input' and nombre:
            tipo = (a.get('type') or 'text').lower()
            if tipo == 'hidden':
                if nombre != 'csrf_token':
                    f['envia'].add((nombre, a.get('value', '')))
            elif tipo in ('checkbox', 'radio'):
                f['editables'].add(nombre)
                f['opciones'].add((nombre, a.get('value', 'on')))
                if 'checked' in a:
                    f['envia'].add((nombre, a.get('value', 'on')))
            elif tipo not in ('submit', 'button'):
                f['editables'].add(nombre)
        elif tag in ('select', 'textarea') and nombre:
            f['editables'].add(nombre)
        elif tag == 'button' and nombre:
            f['envia'].add((nombre, a.get('value', '')))

    def handle_endtag(self, tag):
        if tag == 'form':
            self._f = None


def formularios(html):
    p = _Formularios()
    p.feed(html)
    return p.forms


def firma(f):
    """Representación comparable de un formulario."""
    return {
        'action': f['action'], 'method': f['method'], 'enctype': f['enctype'],
        'editables': sorted(f['editables']), 'envia': sorted([list(x) for x in f['envia']]),
        'opciones': sorted([list(x) for x in f['opciones']]),
    }


def contexto(con_bd=True):
    """Contexto que activa todas las ramas de la plantilla."""
    import module_service as ms
    import tenant_site_fields as tsf
    import timezone_service as tzs
    import client_config_service as ccs
    from routes.tenant_routes import PLANTILLAS_SITIO

    activos = {'pos', 'orders', 'inventory', 'ai_assistant', 'ai_public', 'crm'}
    mods = [{'code': c, 'nombre': n, 'descripcion': d, 'categoria': cat, 'is_active': c in activos}
            for c, n, d, cat, _k, _def in ms.MODULES]
    tenant = {'id': 7, 'slug': 'cliente-a', 'nombre': 'Cliente A', 'db_name': 'cyber_t007' if con_bd else None,
              'estado': 'activo', 'plan': 'ultra', 'db_host': 'localhost', 'db_port': 5432,
              'schema_version': 15, 'created_at': datetime(2026, 1, 2, 3, 4)}
    integraciones = []
    for grupo, campos in __import__('integrations_service').GROUPS:
        items = []
        for key, label, secret, ftype, options in campos:
            items.append({'key': key, 'label': label, 'secret': secret,
                          'type': 'modelos' if key == 'AI_MODEL' else ftype,
                          'options': ['modelo-a'] if key == 'AI_MODEL' else options,
                          'value': '' if secret else 'x', 'masked': '••••' if secret else '',
                          'has_value': True})
        integraciones.append({'group': grupo, 'fields': items})
    billing = {
        'estado': 'mora', 'proxima_fecha': date(2026, 9, 1), 'dias': 12, 'auto_suspender': True,
        'a_suspension': 3, 'umbral_suspension': 15, 'monto_mensual': 120000, 'en_mora': True,
        'ultimo_pago': {'monto': 120000, 'fecha': date(2026, 8, 1), 'metodo': 'transferencia'},
        'motor': {'es_trial': True, 'suspendida_por_pago': False, 'buyer_email': 'a@b.co',
                  'buyer_nombre': 'Ana', 'buyer_telefono': '3001234567', 'whatsapp_url': 'https://wa.me/573001234567',
                  'plan_key': 'ultra', 'proximo_pago': date(2026, 9, 1), 'ultimo_recordatorio': 'd-1',
                  'link_pago': 'https://x/pagar'},
        'aviso_modo': 'auto', 'dias_suspension': None, 'notas': 'nota',
        'historial': [{'fecha': date(2026, 8, 1), 'monto': 120000, 'metodo': 'efectivo',
                       'cubre_hasta': date(2026, 9, 1), 'nota': '', 'registrado_por': 'op'}],
    }
    cfg = {'values': {f['key']: '' for f in tsf.SITE_FIELDS}} if con_bd else None
    return dict(
        tenant=tenant,
        keys=[{'id': 1, 'active': True, 'label': 'POS', 'client_code': 'C1', 'key_prefix': 'abc',
               'created_at': datetime(2026, 1, 1), 'last_used_at': datetime(2026, 9, 1)},
              {'id': 2, 'active': False, 'label': 'Viejo', 'client_code': 'C2', 'key_prefix': 'def',
               'created_at': datetime(2026, 1, 1), 'last_used_at': None}],
        health={'service_active': True, 'http_ok': True, 'status': 'ok', 'db': 'ok', 'redis': 'ok', 'detail': ''},
        plantilla_actual='clasico', plantillas_sitio=PLANTILLAS_SITIO,
        cfg=cfg, secs={k: True for k, _ in ccs.SECTION_FIELDS} if con_bd else None,
        mods=mods if con_bd else None, site_error=None,
        acciones_ia=[{'decidido_en': datetime(2026, 9, 1), 'creado_en': None, 'usuario_id': 1,
                      'tipo': 'crear_producto', 'estado': 'confirmada', 'resumen': 'Producto X'}] if con_bd else None,
        integraciones=integraciones,
        dian={'master_configured': True, 'service_url': 'https://dian/api/v1',
              'env': {'DIAN_SERVICE_URL': True, 'DIAN_API_KEY': False}, 'env_ok': False,
              'prefill': {'nit': '123', 'razon_social': 'Cliente A'}},
        runtime={'port': 5007, 'subdomain': 'cliente-a', 'custom_domain': 'cliente.com', 'instance_status': 'running'},
        proxy_preview='server { }', server_ip='1.2.3.4', proxy_backend='nginx', primary_slug='cliente-a',
        site_fields=tsf.SITE_FIELDS, site_groups=tsf.SITE_GROUPS, section_fields=ccs.SECTION_FIELDS,
        plans=ms.PLANS, billing=billing, restaurante_simple=False,
        auditoria=[{'ts': datetime(2026, 9, 1, 10, 0), 'accion': 'pago', 'actor': 'op', 'detalle': ''}],
        timezones=tzs.TIMEZONES, tz_actual='America/Bogota',
    )


def render(con_bd=True):
    import os
    os.environ.setdefault('FLASK_SECRET_KEY', 'form-contract-test-only-secret')
    from flask import render_template
    from app import create_app
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SERVER_NAME='admin.local')
    with app.test_request_context('/tenants/7'):
        return render_template('tenant_detail.html', admin={'nombre': 'Op', 'email': 'op@x.co'},
                               **contexto(con_bd))
