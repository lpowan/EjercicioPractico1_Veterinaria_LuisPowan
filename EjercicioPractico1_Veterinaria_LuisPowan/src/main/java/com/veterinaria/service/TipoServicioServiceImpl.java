package com.veterinaria.service;

import com.veterinaria.domain.TipoServicio;
import com.veterinaria.repository.TipoServicioRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TipoServicioServiceImpl implements TipoServicioService {

    private final TipoServicioRepository tipoServicioRepository;

    public TipoServicioServiceImpl(TipoServicioRepository tipoServicioRepository) {
        this.tipoServicioRepository = tipoServicioRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public List<TipoServicio> listarTipos() {
        return tipoServicioRepository.findAllByOrderByNombreAsc();
    }

    @Override
    @Transactional(readOnly = true)
    public TipoServicio buscarTipo(Integer idTipo) {
        return tipoServicioRepository.findById(idTipo).orElse(null);
    }

    @Override
    @Transactional
    public void guardarTipo(TipoServicio tipoServicio) {
        tipoServicio.setNombre(tipoServicio.getNombre().trim());
        String descripcion = tipoServicio.getDescripcion();
        tipoServicio.setDescripcion(descripcion == null || descripcion.isBlank() ? null : descripcion.trim());
        tipoServicioRepository.save(tipoServicio);
    }

    @Override
    @Transactional
    public boolean eliminarTipo(Integer idTipo) {
        TipoServicio tipoServicio = tipoServicioRepository.findById(idTipo).orElse(null);
        // Regla de negocio: no se elimina un tipo que todavia tiene servicios
        if (tipoServicio == null || !tipoServicio.getServicios().isEmpty()) {
            return false;
        }
        tipoServicioRepository.delete(tipoServicio);
        return true;
    }
}
