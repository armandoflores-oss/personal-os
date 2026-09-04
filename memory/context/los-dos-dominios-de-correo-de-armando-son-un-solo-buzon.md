---
titulo: Los dos dominios de correo de Armando son un solo buzón
creada: 2026-09-04
---

# Los dos dominios de correo de Armando son un solo buzón

- 2026-09-04 — armando.flores@draiver.com y armando.flores@driverdo.com entregan al MISMO buzón: no son dos cuentas. Validado por Armando el 2026-09-04. Consecuencia: el ingest de Gmail del Personal OS ve el correo de ambos dominios y NO hay punto ciego por dominio. El header Delivered-To siempre queda como draiver.com (driverdo.com se resuelve antes de la entrega), así que buscar con deliveredto:...@driverdo.com da cero y eso es normal, no una falta de correo.  <!-- feedback:fact -->
