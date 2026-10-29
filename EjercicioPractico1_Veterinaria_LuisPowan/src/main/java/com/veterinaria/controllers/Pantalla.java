package com.veterinaria.controllers;

import org.springframework.ui.Model;

// Todas las paginas se muestran dentro de la plantilla base "plantilla/marco"
final class Pantalla {

    private static final String PLANTILLA_BASE = "plantilla/marco";

    private Pantalla() {
    }

    // vista: carpeta/archivo dentro de templates/vistas; claveTitulo: clave de messages.properties
    static String mostrar(Model model, String vista, String claveTitulo) {
        model.addAttribute("vista", "vistas/" + vista);
        model.addAttribute("claveTitulo", claveTitulo);
        return PLANTILLA_BASE;
    }
}
