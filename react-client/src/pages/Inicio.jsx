// src/pages/Inicio.jsx (FINAL)

import DashboardStats from "../components/DashboardStats.jsx";

export default function Inicio({ user }) {
  return (
    <>
      <h1 className="welcome-title">Bienvenido, {user.nombre_completo}</h1>
      {/* DashboardStats es ahora el componente contenedor que carga y renderiza todo */}
      <DashboardStats />
    </>
  );
}