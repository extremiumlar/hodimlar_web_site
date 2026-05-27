"use client";
import useSWR from "swr";
import { api } from "@/lib/api";
import { useMe } from "@/lib/useMe";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Title, Tooltip, Legend, ArcElement,
} from "chart.js";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, ArcElement);

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export default function AdminPage() {
  const router = useRouter();
  const { me, isHR, isLoading } = useMe();
  const { data: live } = useSWR("/attendance/live/", fetcher, { refreshInterval: 15000 });
  const { data: stats } = useSWR("/attendance/stats/?days=30", fetcher);

  useEffect(() => {
    if (!isLoading && me && !isHR) router.replace("/dashboard");
  }, [isLoading, me, isHR, router]);

  if (!isHR) return null;

  const byDay = stats?.by_day || [];
  const lateTop = stats?.late_top || [];
  const workedTop = stats?.worked_top || [];

  const lineData = {
    labels: byDay.map((d: any) => d.date),
    datasets: [
      { label: "Keldi", data: byDay.map((d: any) => d.present), borderColor: "#10b981", backgroundColor: "#10b98133", tension: 0.3 },
      { label: "Kechikdi", data: byDay.map((d: any) => d.late), borderColor: "#f59e0b", backgroundColor: "#f59e0b33", tension: 0.3 },
    ],
  };

  const lateBar = {
    labels: lateTop.map((u: any) => `${u.user__first_name || ""} ${u.user__last_name || u.user__username}`.trim()),
    datasets: [{ label: "Kechikish (daq)", data: lateTop.map((u: any) => u.late_total_min || 0), backgroundColor: "#ef4444" }],
  };

  const workedBar = {
    labels: workedTop.map((u: any) => `${u.user__first_name || ""} ${u.user__last_name || u.user__username}`.trim()),
    datasets: [{ label: "Ishlangan (daq)", data: workedTop.map((u: any) => u.worked || 0), backgroundColor: "#3b82f6" }],
  };

  const doughnut = {
    labels: ["Ofisda", "Yo'q", "Ta'tilda"],
    datasets: [{
      data: [live?.in_office?.length || 0, live?.absent?.length || 0, live?.on_leave?.length || 0],
      backgroundColor: ["#10b981", "#ef4444", "#f59e0b"],
    }],
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin panel</h1>
        <p className="text-slate-500">Real vaqtda hodimlar holati</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-sm text-slate-500">Hozir ofisda</div>
          <div className="text-3xl font-bold text-emerald-600 mt-1">{live?.in_office?.length || 0}</div>
        </div>
        <div className="card">
          <div className="text-sm text-slate-500">Bugun yo'q</div>
          <div className="text-3xl font-bold text-rose-600 mt-1">{live?.absent?.length || 0}</div>
        </div>
        <div className="card">
          <div className="text-sm text-slate-500">Ta'tilda</div>
          <div className="text-3xl font-bold text-amber-600 mt-1">{live?.on_leave?.length || 0}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h2 className="font-semibold mb-3">30 kunlik davomat</h2>
          <Line data={lineData} options={{ responsive: true, plugins: { legend: { position: "bottom" } } }} />
        </div>
        <div className="card">
          <h2 className="font-semibold mb-3">Hozirgi holat</h2>
          <Doughnut data={doughnut} options={{ plugins: { legend: { position: "bottom" } } }} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Eng ko'p kechikadiganlar</h2>
          <Bar data={lateBar} options={{ indexAxis: "y" as const, plugins: { legend: { display: false } } }} />
        </div>
        <div className="card">
          <h2 className="font-semibold mb-3">Eng ko'p ishlaganlar</h2>
          <Bar data={workedBar} options={{ indexAxis: "y" as const, plugins: { legend: { display: false } } }} />
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-3">Hozir ofisda</h2>
        <table className="w-full text-sm">
          <thead className="text-slate-500">
            <tr className="border-b">
              <th className="text-left py-2">Hodim</th>
              <th className="text-left py-2">Kelgan</th>
              <th className="text-left py-2">Kechikish</th>
              <th className="text-left py-2">IP</th>
            </tr>
          </thead>
          <tbody>
            {live?.in_office?.map((a: any) => (
              <tr key={a.id} className="border-b last:border-0">
                <td className="py-2">{a.user_name}</td>
                <td>{new Date(a.check_in_time).toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" })}</td>
                <td>{a.late_minutes > 0 ? <span className="text-rose-600">{a.late_minutes} daq</span> : "—"}</td>
                <td className="text-slate-500">{a.check_in_ip}</td>
              </tr>
            ))}
            {!live?.in_office?.length && <tr><td colSpan={4} className="py-4 text-center text-slate-400">Hozir ofisda hech kim yo'q.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
