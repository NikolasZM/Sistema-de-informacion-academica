// src/components/DashboardStats.jsx (ACTUALIZADO)
import { useEffect, useState } from "react"
import { FaClock, FaExclamationTriangle, FaCalendarAlt, FaExternalLinkAlt, FaGraduationCap } from 'react-icons/fa';
import HorarioSemanal from "./HorarioSemanal.jsx"; // Importamos el horario

const UPLOAD_PERCENT_LIMIT = 30; // 30% de inasistencia

function DashboardContent({ stats }) {
    const isAtRisk = stats.porcentaje_inasistencia >= UPLOAD_PERCENT_LIMIT;

    const cards = [
        { 
            title: "Inasistencia Total", 
            value: `${stats.porcentaje_inasistencia.toFixed(1)}%`, 
            hint: `${stats.faltas_no_justificadas} faltas no justificadas` ,
            cls: isAtRisk ? 'danger' : (stats.porcentaje_inasistencia > 15 ? 'warning' : 'ok')
        },
        { 
            title: "Período Activo", 
            value: stats.periodo_codigo, 
            hint: `Inicio: ${stats.fecha_matricula}`,
            cls: 'info'
        },
        { 
            title: "Cursos Actuales", 
            value: stats.cursos_activos_total, 
            hint: `En ${stats.programa_nombre}`,
            cls: 'info'
        },
        { 
            title: "Módulos Aprobados", 
            value: stats.modulos_aprobados_conteo, 
            hint: "Para certificación",
            cls: 'success'
        },
    ];

    return (
        <>
            {isAtRisk && (
                <div className="alert alert-danger">
                    <FaExclamationTriangle /> ¡ALERTA CRÍTICA! Has superado el {UPLOAD_PERCENT_LIMIT}% de inasistencia ({stats.faltas_no_justificadas} faltas no justificadas). Riesgo de **RETIRO AUTOMÁTICO**.
                </div>
            )}
            
            {/* --- CUADRO DE ESTADÍSTICAS --- */}
            <section className="dashboard-grid">
                {cards.map((c, i) => (
                    <article className={`stat-card ${c.cls}`} key={i}>
                        <div className="stat-title">{c.title}</div>
                        <div className="stat-value">{c.value}</div>
                        <div className="stat-hint">{c.hint}</div>
                    </article>
                ))}
            </section>

            <div className="dashboard-layout">
                {/* --- HORARIO --- */}
                <div className="dashboard-schedule">
                    <HorarioSemanal 
                        programaciones={stats.horario_activo}
                        titulo="Horario de Clases Activo"
                        periodo={stats.periodo_codigo}
                    />
                </div>
                
                {/* --- LINKS ÚTILES --- */}
                <div className="dashboard-sidebar">
                    <h3 className="sidebar-title"><FaExternalLinkAlt /> Recursos Rápidos</h3>
                    <ul className="quick-links">
                        {stats.links_utiles.map((link, i) => (
                            <li key={i}>
                                <a href={link.url} target="_blank" rel="noopener noreferrer">{link.nombre}</a>
                            </li>
                        ))}
                    </ul>
                    
                    <h3 className="sidebar-title mt-4"><FaGraduationCap /> Contexto</h3>
                    <p><strong>Programa:</strong> {stats.programa_nombre}</p>
                    <p><strong>Matrícula:</strong> {stats.fecha_matricula}</p>
                    <p><strong>Total Sesiones:</strong> {stats.total_sesiones}</p>
                </div>
            </div>
        </>
    );
}

export default function DashboardStats() {
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        setLoading(true)
        // 👈 Nueva API consolidada
        fetch("/api/estudiante/dashboard_full", { credentials: "include" })
        .then(async (res) => {
            if (!res.ok) {
                const err = await res.json().catch(() => ({}))
                throw new Error(err.error || "No autorizado")
            }
            return res.json()
        })
        .then((data) => {
            setStats(data)
        })
        .catch((e) => {
            setError(e.message)
        })
        .finally(() => setLoading(false))
    }, [])

    if (loading) return <div className="panel loading">Cargando estadísticas…</div>
    if (error) return <div className="panel error">Error: {error}</div>
    if (!stats) return null

    return <DashboardContent stats={stats} />;
}