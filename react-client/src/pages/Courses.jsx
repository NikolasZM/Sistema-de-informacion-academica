// Courses.jsx
import { useEffect, useState } from "react"
import { FaChevronDown, FaChevronUp } from "react-icons/fa"

/* -------------------------- SessionRows -------------------------- */
function SessionRows({ sessions }) {
  // Aseguramos que las horas se muestren correctamente
  const formatTime = (timeStr) => {
      if (!timeStr) return "";
      try {
          // Asume que la hora viene en formato HH:MM:SS
          const [h, m] = timeStr.split(':');
          return `${h}:${m}`;
      } catch {
          return timeStr;
      }
  };

  return sessions.map((s, i) => (
    <tr key={i} className="course-detail">
      {/* Celdas vacías para alineación con las columnas principales */}
      <td className="detail-align"></td> 
      <td className="detail-align"></td>
      <td className="detail-align"></td>
      
      {/* Columnas de detalle */}
      <td className="detail-col-header">{s.dia_semana}</td>
      <td>{`${formatTime(s.hora_inicio) ?? ""}${s.hora_inicio && s.hora_fin ? " - " : ""}${formatTime(s.hora_fin) ?? ""}`}</td>
      <td>{s.salon ?? "Sin aula"}</td>
      <td>{s.docente ?? "Sin asignar"}</td>
      
      <td className="detail-align"></td>
    </tr>
  ))
}

/* -------------------------- CourseRow -------------------------- */
function CourseRow({ idx, course }) {
  const [open, setOpen] = useState(false)

  // Usamos el docente de la primera sesión como "principal"
  const mainTeacher = (course.programaciones && course.programaciones.find(p => p.docente))?.docente || "Sin asignar"

  return (
    <>
      <tr className="course-row">
        <td>{idx + 1}</td>
        <td>{course.modulo_nombre}</td>
        <td>{course.nombre}</td>
        <td>{mainTeacher}</td>
        <td>
          <button className="course-btn" onClick={() => setOpen(v => !v)}>
            {open ? "Ocultar" : "Ver horario"} {open ? <FaChevronUp /> : <FaChevronDown />}
          </button>
        </td>
      </tr>
      {/* 💡 Mostrar el detalle del horario si está abierto */}
      {open && course.programaciones && course.programaciones.length > 0 ? (
          <SessionRows sessions={course.programaciones} />
      ) : (
          open && <tr className="course-detail"><td colSpan="5">No hay horario asignado.</td></tr>
      )}
    </>
  )
}

/* -------------------------- Main component -------------------------- */
export default function Courses() {
  const [periodCode, setPeriodCode] = useState(null) // Para mostrar el período detectado
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Cargar cursos del período actual
  useEffect(() => {
    setLoading(true)
    // 💡 Nueva API: /api/estudiante/cursos_actuales
    fetch("/api/estudiante/cursos_actuales", { credentials: "include" })
      .then(async res => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.error || "No autenticado o error del servidor")
        }
        return res.json()
      })
      .then(data => {
        setPeriodCode(data.periodo_codigo) // Guardar el código del período detectado
        setCourses(data.cursos) // Guardar la lista de cursos
      })
      .catch(err => {
        console.error("Error cargando cursos:", err)
        setError(err.message || "Error al cargar cursos")
        setCourses([])
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <section className="courses-page">
      <h1>Horario y Docentes</h1>

      {loading ? (
        <p>Detectando período y cargando cursos...</p>
      ) : error ? (
        <p style={{ color: "red" }}>{error}</p>
      ) : (
        <>
          {/* 💡 Muestra el período detectado, no hay selector */}
          <div className="module-card">
             {periodCode ? (
                <h2>Período Detectado: {periodCode}</h2>
             ) : (
                <h2>No hay período con matrícula activa.</h2>
             )}
          </div>

          <div className="courses-wrapper">
            <table className="courses-table">
              <thead>
                <tr>
                  <th>Nº</th>
                  <th>Módulo</th> 
                  <th>Unidad Didáctica</th>
                  <th>Docente Principal</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {courses.length > 0 ? (
                  courses.map((c, i) => <CourseRow key={c.id} idx={i} course={c} />)
                ) : (
                  <tr><td colSpan="5">No estás matriculado en cursos activos para este período.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  )
}