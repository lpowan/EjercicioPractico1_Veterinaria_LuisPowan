package com.veterinaria.service;

import com.veterinaria.domain.Servicio;
import java.util.List;

public interface ServicioService {

    List<Servicio> listarServicios();

    // Devuelve null si el servicio no existe
    Servicio buscarServicio(Integer idServicio);

    // Devuelve false si el tipo de servicio seleccionado no existe
    boolean guardarServicio(Servicio servicio);

    // Devuelve false si el servicio no existe o tiene citas programadas
    boolean eliminarServicio(Integer idServicio);
}
