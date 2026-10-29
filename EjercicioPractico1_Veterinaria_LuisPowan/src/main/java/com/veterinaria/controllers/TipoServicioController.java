package com.veterinaria.controllers;

import com.veterinaria.domain.TipoServicio;
import com.veterinaria.service.TipoServicioService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/tipos")
public class TipoServicioController {

    private final TipoServicioService tipoServicioService;

    public TipoServicioController(TipoServicioService tipoServicioService) {
        this.tipoServicioService = tipoServicioService;
    }

    @GetMapping
    public String mostrarTipos(Model model) {
        model.addAttribute("tipos", tipoServicioService.listarTipos());
        return Pantalla.mostrar(model, "tipos/listado", "tipos.titulo");
    }

    @GetMapping("/nuevo")
    public String mostrarFormularioNuevo(Model model) {
        model.addAttribute("tipoServicio", new TipoServicio());
        return Pantalla.mostrar(model, "tipos/formulario", "tipos.titulo");
    }

    @GetMapping("/editar/{idTipo}")
    public String mostrarFormularioEditar(@PathVariable Integer idTipo, Model model,
            RedirectAttributes redirectAttributes) {
        TipoServicio tipoServicio = tipoServicioService.buscarTipo(idTipo);
        if (tipoServicio == null) {
            redirectAttributes.addFlashAttribute("mensajeError", "tipos.mensaje.noEncontrado");
            return "redirect:/tipos";
        }
        model.addAttribute("tipoServicio", tipoServicio);
        return Pantalla.mostrar(model, "tipos/formulario", "tipos.titulo");
    }

    @PostMapping("/guardar")
    public String guardarTipo(@ModelAttribute TipoServicio tipoServicio,
            RedirectAttributes redirectAttributes) {
        boolean esNuevo = tipoServicio.getId() == null;
        tipoServicioService.guardarTipo(tipoServicio);
        redirectAttributes.addFlashAttribute("mensajeExito",
                esNuevo ? "tipos.mensaje.agregado" : "tipos.mensaje.modificado");
        return "redirect:/tipos";
    }

    @PostMapping("/eliminar")
    public String eliminarTipo(@RequestParam("id") Integer idTipo,
            RedirectAttributes redirectAttributes) {
        if (tipoServicioService.eliminarTipo(idTipo)) {
            redirectAttributes.addFlashAttribute("mensajeExito", "tipos.mensaje.eliminado");
        } else {
            redirectAttributes.addFlashAttribute("mensajeError", "tipos.mensaje.noEliminado");
        }
        return "redirect:/tipos";
    }
}
