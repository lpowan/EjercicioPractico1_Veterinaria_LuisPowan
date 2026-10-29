package com.veterinaria.controllers;

import com.veterinaria.domain.Consulta;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/consultas")
public class ConsultaController {

    @GetMapping
    public String mostrarFormularioConsulta(Model model) {
        model.addAttribute("consulta", new Consulta());
        return Pantalla.mostrar(model, "consultas/formulario", "consultas.titulo");
    }

    // Solo interfaz: no se guarda en la base de datos
    @PostMapping("/enviar")
    public String enviarConsulta(@ModelAttribute Consulta consulta,
            RedirectAttributes redirectAttributes) {
        redirectAttributes.addFlashAttribute("consultaEnviada", consulta);
        redirectAttributes.addFlashAttribute("mensajeExito", "consultas.mensaje.enviada");
        return "redirect:/consultas";
    }
}
