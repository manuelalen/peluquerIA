USE dev_testeos;

CREATE TABLE citas_crm(
id_cliente int not null,
fecha_cita TIMESTAMP not null,
Servicio VARCHAR(99)
);

ALTER TABLE citas_crm add column hora_cita varchar(9);

select cc.id_cliente,cl.nombre_completo, cc.fecha_cita, cc.hora_cita, cc.Servicio
from citas_crm cc
 join clientes cl
on cc.id_cliente = cl.id_cliente;

CREATE TABLE citas_servicios(
id_cliente int,
cita_asistida char(1),
fecha_cita TIMESTAMP,
id_peluquero int,
hora_cita varchar(9),
primary key(id_cliente, id_peluquero)
);
