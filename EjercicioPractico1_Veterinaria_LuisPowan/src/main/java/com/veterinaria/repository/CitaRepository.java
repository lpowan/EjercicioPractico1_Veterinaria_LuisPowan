package com.veterinaria.repository;

import com.veterinaria.domain.Cita;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CitaRepository extends JpaRepository<Cita, Integer> {

    List<Cita> findAllByOrderByFechaAsc();

    boolean existsByServicioId(Integer servicioId);
}
