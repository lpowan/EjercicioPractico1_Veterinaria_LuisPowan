package com.veterinaria.service;

import com.veterinaria.domain.Servicio;
import com.veterinaria.domain.TipoServicio;
import com.veterinaria.repository.CitaRepository;
import com.veterinaria.repository.ServicioRepository;
import com.veterinaria.repository.TipoServicioRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ServicioServiceImpl implements ServicioService {

    private final ServicioRepository servicioRepository;
    private final TipoServicioRepository tipoServicioRepository;
    private final CitaRepository citaRepository;

    public ServicioServiceImpl(ServicioRepository servicioRepository,
            TipoServicioRepository tipoServicioRepository,
            CitaRepository citaRepository) {
        this.servicioRepository = servicioRepository;
        this.tipoServicioRepository = tipoServicioRepository;
        this.citaRepository = citaRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public List<Servicio> listarServicios() {
        return servicioRepository.findAllByOrderByNombreAsc();
    }

    @Override
    @Transactional(readOnly = true)
    public Servicio buscarServicio(Integer idServicio) {
        return servicioRepository.findById(idServicio).orElse(null);
    }

    @Override
    @Transactional
    public boolean guardarServicio(Servicio servicio) {
        if (servicio.getTipoServicio() == null || servicio.getTipoServicio().getId() == null) {
            return false;
        }
        // Se asigna el tipo real de la base de datos a partir del id seleccionado
        TipoServicio tipoServicio = tipoServicioRepository.findById(servicio.getTipoServicio().getId()).orElse(null);
        if (tipoServicio == null) {
            return false;
        }
        servicio.setTipoServicio(tipoServicio);
        servicio.setNombre(servicio.getNombre().trim());
        servicioRepository.save(servicio);
        return true;
    }

    @Override
    @Transactional
    public boolean eliminarServicio(Integer idServicio) {
        // Regla de negocio: no se elimina un servicio con citas programadas
        if (!servicioRepository.existsById(idServicio) || citaRepository.existsByServicioId(idServicio)) {
            return false;
        }
        servicioRepository.deleteById(idServicio);
        return true;
    }
}
