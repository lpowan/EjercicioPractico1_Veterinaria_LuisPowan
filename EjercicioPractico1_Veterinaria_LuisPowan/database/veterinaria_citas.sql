-- ======================================
-- 1) CREAR USUARIO
-- ======================================
DROP USER IF EXISTS 'usuario_caso_practico_01_var'@'localhost';
CREATE USER 'usuario_caso_practico_01_var'@'localhost'
IDENTIFIED BY '123456';

-- ======================================
-- 2) CREAR BASE DE DATOS
-- ======================================
DROP DATABASE IF EXISTS veterinaria_citas;
CREATE DATABASE veterinaria_citas;
GRANT ALL PRIVILEGES ON veterinaria_citas.*
TO 'usuario_caso_practico_01_var'@'localhost';
FLUSH PRIVILEGES;
USE veterinaria_citas;

-- ======================================
-- 3) TABLA TIPO_SERVICIO
-- ======================================
CREATE TABLE tipo_servicio (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  descripcion VARCHAR(255)
);

-- ======================================
-- 4) TABLA SERVICIO
-- ======================================
CREATE TABLE servicio (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  precio DECIMAL(8,2) NOT NULL,
  duracion_minutos INT NOT NULL,
  tipo_servicio_id INT NOT NULL,
  FOREIGN KEY (tipo_servicio_id) REFERENCES tipo_servicio(id)
);

-- ======================================
-- 5) TABLA CITA
-- ======================================
CREATE TABLE cita (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre_mascota VARCHAR(100) NOT NULL,
  nombre_propietario VARCHAR(100) NOT NULL,
  fecha DATE NOT NULL,
  servicio_id INT NOT NULL,
  FOREIGN KEY (servicio_id) REFERENCES servicio(id)
);

-- ======================================
-- 6) DATOS DE PRUEBA
-- ======================================
-- Tipos de servicio
INSERT INTO tipo_servicio (nombre, descripcion) VALUES
('Consulta General', 'Revisión médica y diagnóstico'),
('Vacunación', 'Esquemas de vacunas y refuerzos'),
('Estética', 'Baño, corte y cuidado de pelaje'),
('Cirugía', 'Procedimientos quirúrgicos programados');

-- Servicios
INSERT INTO servicio (nombre, precio, duracion_minutos, tipo_servicio_id) VALUES
('Consulta Medicina General', 18000.00, 30, 1),
('Control de Peso y Nutrición', 15000.00, 30, 1),
('Vacuna Antirrábica', 12500.00, 15, 2),
('Vacuna Polivalente Canina', 16000.00, 15, 2),
('Baño y Corte Raza Pequeña', 14000.00, 60, 3),
('Esterilización Felina', 65000.00, 90, 4);

-- Citas
INSERT INTO cita (nombre_mascota, nombre_propietario, fecha, servicio_id) VALUES
('Max', 'Carolina Jiménez', '2026-11-04', 1),
('Luna', 'Diego Vargas', '2026-11-06', 3),
('Toby', 'Mariana Rojas', '2026-11-09', 5),
('Michi', 'Esteban Quesada', '2026-11-12', 6);

-- Fin del Script
