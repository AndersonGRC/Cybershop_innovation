"""Cron diario: borra las copias de respaldo de pruebas gratis ELIMINADAS que
nunca pagaron, con más de 30 días. Las de clientes que pagaron no se tocan.

    python tools/purgar_backups_pruebas.py            # vista previa
    python tools/purgar_backups_pruebas.py --aplicar  # borra
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lifecycle_service as lc  # noqa: E402

if __name__ == '__main__':
    if '--aplicar' in sys.argv:
        archivos, total = lc.purgar_backups_pruebas(actor='cron')
        print(f'Borradas {archivos} copias ({round(total / 1048576, 1)} MB).')
    else:
        lista = lc.backups_pruebas_vencidos()
        print(f'Se borrarían {len(lista)} copias:')
        for b in lista:
            print('  -', b['ruta'], b['bytes'], 'bytes')
