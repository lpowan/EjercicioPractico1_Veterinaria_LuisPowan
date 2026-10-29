package com.veterinaria.controllers;

import com.veterinaria.domain.Servicio;
import com.veterinaria.domain.TipoServicio;
import com.veterinaria.service.ServicioService;
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
@RequestMapping("/servicios")
public class ServicioController {

    private final ServicioService servicioService;
    private final TipoServicioService tipoServicioService;

    public ServicioController(ServicioService servicioService, TipoServicioService tipoServicioService) {
        this.servicioService = servicioService;
        this.tipoServicioService = tipoServicioService;
    }

    @GetMapping
    public String mostrarServicios(Model model) {
        model.addAttribute("servicios", servicioService.listarServicios());
        return Pantalla.mostrar(model, "servicios/listado", "servicios.titulo");
    }

    @GetMapping("/nuevo")
    public String mostrarFormularioNuevo(Model model) {
        Servicio servicio = new Servicio();
        servicio.setTipoServicio(new TipoServicio());
        model.addAttribute("servicio", servicio);
        model.addAttribute("tipos", tipoServicioService.listarTipos());
        return Pantalla.mostrar(model, "servicios/formulario", "servicios.titulo");
    }

    @GetMapping("/editar/{idServicio}")
    public String mostrarFormularioEditar(@PathVariable Integer idServicio, Model model,
            RedirectAttributes redirectAttributes) {
        Servicio servicio = servicioService.buscarServicio(idServicio);
        if (servicio == null) {
            redirectAttributes.addFlashAttribute("mensajeError", "servicios.mensaje.noEncontrado");
            return "redirect:/servicios";
        }
        model.addAttribute("servicio", servicio);
        model.addAttribute("tipos", tipoServicioService.listarTipos());
        return Pantalla.mostrar(model, "servicios/formulario", "servicios.titulo");
    }

    @PostMapping("/guardar")
    public String guardarServicio(@ModelAttribute Servicio servicio,
            RedirectAttributes redirectAttributes) {
        boolean esNuevo = servicio.getId() == null;
        if (servicioService.guardarServicio(servicio)) {
            redirectAttributes.addFlashAttribute("mensajeExito",
                    esNuevo ? "servicios.mensaje.agregado" : "servicios.mensaje.modificado");
        } else {
            redirectAttributes.addFlashAttribute("mensajeError", "servicios.mensaje.tipoInvalido");
        }
        return "redirect:/servicios";
    }

    @PostMapping("/eliminar")
    public String eliminarServicio(@RequestParam("id") Integer idServicio,
            RedirectAttributes redirectAttributes) {
        if (servicioService.eliminarServicio(idServicio)) {
            redirectAttributes.addFlashAttribute("mensajeExito", "servicios.mensaje.eliminado");
        } else {
            redirectAttributes.addFlashAttribute("mensajeError", "servicios.mensaje.noEliminado");
        }
        return "redirect:/servicios";
    }
}
