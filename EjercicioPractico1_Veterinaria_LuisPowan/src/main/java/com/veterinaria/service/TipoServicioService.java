package com.veterinaria.service;

import com.veterinaria.domain.TipoServicio;
import java.util.List;

public interface TipoServicioService {

    List<TipoServicio> listarTipos();

    // Devuelve null si el tipo no existe
    TipoServicio buscarTipo(Integer idTipo);

    void guardarTipo(TipoServicio tipoServicio);

    // Devuelve false si el tipo no existe o tiene servicios asociados
    boolean eliminarTipo(Integer idTipo);
}
