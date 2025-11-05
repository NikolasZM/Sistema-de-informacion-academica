// src/components/HorarioSemanal.jsx
import React from 'react';
import { FaClock, FaCalendarAlt, FaChalkboard, FaUserTie } from 'react-icons/fa';

// Define el orden de los días de la semana
const DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];

/* ------------------------------------------------------- */
/* Utilidad: Organiza los datos por día de la semana       */
/* ------------------------------------------------------- */
const organizarPorDia = (programaciones) => {
    const horario = {};
    DIAS_SEMANA.forEach(dia => {
        horario[dia] = [];
    });
    
    // Asumimos que programaciones es un array de objetos con: 
    // { dia_semana, hora_inicio, hora_fin, curso_nombre, docente, salon }
    programaciones.forEach(prog => {
        if (horario[prog.dia_semana]) {
            horario[prog.dia_semana].push(prog);
        }
    });

    // Ordenar los cursos por hora de inicio dentro de cada día
    Object.keys(horario).forEach(dia => {
        horario[dia].sort((a, b) => {
            // Comparación simple de strings de tiempo (ej. "08:00" vs "10:00")
            if (a.hora_inicio < b.hora_inicio) return -1;
            if (a.hora_inicio > b.hora_inicio) return 1;
            return 0;
        });
    });

    return horario;
};


/* ------------------------------------------------------- */
/* Componente Principal Responsive                         */
/* ------------------------------------------------------- */
export default function HorarioSemanal({ programaciones, titulo, periodo }) {
    
    // Organiza los datos antes de renderizar
    const horarioOrganizado = organizarPorDia(programaciones);

    return (
        <section className="horario-container">
            <h2><FaCalendarAlt /> {titulo || "Horario Semanal"}</h2>
            {periodo && <p className="periodo-context">**Período:** {periodo}</p>}

            {programaciones.length === 0 ? (
                <p className="no-data">No hay programaciones de clase activas para mostrar.</p>
            ) : (
                
                <table className="horario-table responsive-table">
                    <thead>
                        <tr>
                            <th>Hora</th>
                            {DIAS_SEMANA.map(dia => (
                                <th key={dia}>{dia}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {/* Generamos las filas basadas en todas las horas únicas */}
                        {Object.keys(horarioOrganizado).map(dia => horarioOrganizado[dia])
                            .flat()
                            .filter((value, index, self) => 
                                index === self.findIndex((t) => (
                                    t.hora_inicio === value.hora_inicio && t.hora_fin === value.hora_fin
                                ))
                            ) // Filtra para obtener solo las horas únicas
                            .sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio)) // Ordena por hora
                            .map((uniqueProg, index) => (
                                <tr key={index} className="horario-row">
                                    <td className="time-cell">
                                        {uniqueProg.hora_inicio} - {uniqueProg.hora_fin}
                                    </td>
                                    {DIAS_SEMANA.map(dia => {
                                        // Encuentra el curso que coincide con esta hora y día
                                        const curso = horarioOrganizado[dia].find(p => 
                                            p.hora_inicio === uniqueProg.hora_inicio && p.hora_fin === uniqueProg.hora_fin
                                        );
                                        return (
                                            <td key={dia} className={curso ? "course-cell active" : "course-cell empty"}>
                                                {curso ? (
                                                    <div className="course-content">
                                                        <strong className="course-name">{curso.curso_nombre}</strong>
                                                        <span className="course-detail"><FaChalkboard /> {curso.salon}</span>
                                                        <span className="course-detail"><FaUserTie /> {curso.docente}</span>
                                                    </div>
                                                ) : (
                                                    <span></span>
                                                )}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                    </tbody>
                </table>
            )}
        </section>
    );
}