# Códigos de grupo en las votaciones (campo `grupo`)

Estado: parcial. Verificado en la legislatura X (2011-2016) con las votaciones descargadas. Pendiente completar XI a XV cuando termine la descarga.

Equivalencias de la X (Leg10), inferidas por nombre de grupo y por la composición oficial en `grupos_por_legislatura.json`:

| Código XML | Grupo parlamentario (X)            |
|------------|-------------------------------------|
| GP         | Popular                             |
| GS         | Socialista                          |
| GC-CiU     | Catalán (CiU)                       |
| GV (EAJ-PNV) | Vasco (EAJ-PNV)                   |
| GIP        | La Izquierda Plural                 |
| GUPyD      | Unión Progreso y Democracia         |
| GMx        | Mixto                               |
| (vacío)    | Sin grupo registrado en esa votación (ver nota) |

Nota: el código vacío aparece en unas 259 filas de la X, de diputados como Caamaño Domínguez, Aparicio Pérez o Marcos Domínguez, en votaciones concretas. Se tratan como dato incompleto, no como grupo propio.

Las legislaturas XI-XV usan otros códigos (por ejemplo `GCs`, `GPlu`, `GR`, `GEH Bildu`, `GVOX`, `GCUP-EC-GC`, `GMx`), que hay que confirmar contra la composición oficial de cada legislatura.
