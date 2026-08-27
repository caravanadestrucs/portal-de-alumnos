export function getGradeClass(grade) {
  const num = Number(grade);
  if (grade == null || grade === "" || num === 0 || isNaN(num)) return "badge-neutral";
  if (num >= 9) return "badge-success";
  if (num >= 8) return "badge-warning";
  return "badge-danger";
}
export function getGradeLabel(grade) { if (grade == null || grade === "") return "Sin calificar"; return Number(grade) >= 8 ? "Aprobado" : "Reprobado"; }
export const gradeHierarchy = ["extra_2", "extra_1", "final"];
export function getEffectiveGrade(cal) {
  if (!cal) return { value: null, source: "Ordinaria" };
  const hasExtra2 = cal.extra_2 != null && cal.extra_2 !== "" && Number(cal.extra_2) !== 0;
  const hasExtra1 = cal.extra_1 != null && cal.extra_1 !== "" && Number(cal.extra_1) !== 0;
  if (hasExtra2) return { value: cal.extra_2, source: "Extraordinario 2" };
  if (hasExtra1) return { value: cal.extra_1, source: "Extraordinario 1" };
  const finalVal = cal.calificacion_final ?? cal.final ?? cal.calificacionFinal ?? null;
  return { value: finalVal, source: "Ordinaria" };
}
