c = range(1,13)
print(list(c))

mes = 2
sueldos = 3
meses = 12

mes_index = c.index(mes)

fin = mes_index+(meses-sueldos)


drop_meses = set(c[mes_index:fin])
print(drop_meses)

valid_meses = [m for m in c if m not in drop_meses]
print(valid_meses)

from math import prod

prod_meses = prod(valid_meses)
print(prod_meses)
