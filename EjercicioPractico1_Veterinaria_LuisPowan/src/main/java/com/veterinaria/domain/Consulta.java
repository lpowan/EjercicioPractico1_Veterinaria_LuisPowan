package com.veterinaria.domain;

import java.io.Serializable;

// Objeto del formulario de consultas (no se guarda en la base de datos)
public class Consulta implements Serializable {

    private static final long serialVersionUID = 1L;

    private String nombre;
    private String correo;
    private String nombreMascota;
    private String mensaje;

    public Consulta() {
    }

    public String getNombre() {
        return nombre;
    }

    public void setNombre(String nombre) {
        this.nombre = nombre;
    }

    public String getCorreo() {
        return correo;
    }

    public void setCorreo(String correo) {
        this.correo = correo;
    }

    public String getNombreMascota() {
        return nombreMascota;
    }

    public void setNombreMascota(String nombreMascota) {
        this.nombreMascota = nombreMascota;
    }

    public String getMensaje() {
        return mensaje;
    }

    public void setMensaje(String mensaje) {
        this.mensaje = mensaje;
    }
}
