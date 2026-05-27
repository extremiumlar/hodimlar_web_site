"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Status = "idle" | "loading" | "success" | "error";

function getPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Brauzer geolokatsiyani qo'llab-quvvatlamaydi."));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true, timeout: 10000, maximumAge: 0,
    });
  });
}

export default function CheckInCard() {
  const [att, setAtt] = useState<any>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [msg, setMsg] = useState("");
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    fetchToday();
    return () => clearInterval(t);
  }, []);

  async function fetchToday() {
    try {
      const r = await api.get("/attendance/today/");
      setAtt(r.data);
    } catch {
      setAtt(null);
    }
  }

  async function doCheck(action: "check-in" | "check-out") {
    setStatus("loading");
    setMsg(action === "check-in" ? "Joylashuv aniqlanmoqda..." : "Joylashuv aniqlanmoqda...");
    try {
      const pos = await getPosition();
      const r = await api.post(`/attendance/${action}/`, {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
      });
      setAtt(r.data);
      setStatus("success");
      setMsg(action === "check-in" ? "✅ Keldim deb qayd etildi!" : "✅ Ketdim deb qayd etildi!");
    } catch (e: any) {
      setStatus("error");
      const detail = e.response?.data?.detail || e.message || "Xato yuz berdi.";
      setMsg("❌ " + detail);
    }
  }

  const hasCheckIn = !!att?.check_in_time;
  const hasCheckOut = !!att?.check_out_time;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">Bugungi davomat</h2>
          <p className="text-sm text-slate-500">{time.toLocaleDateString("uz-UZ", { weekday: "long", day: "numeric", month: "long" })}</p>
        </div>
        <div className="text-3xl font-bold text-primary-600 tabular-nums">
          {time.toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-5">
        <div className="bg-slate-50 rounded-lg p-3">
          <div className="text-xs text-slate-500 mb-1">Keldim</div>
          <div className="text-xl font-semibold">{att?.check_in_time ? new Date(att.check_in_time).toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" }) : "—"}</div>
          {att?.late_minutes > 0 && <div className="text-xs text-rose-600 mt-1">Kechikish: {att.late_minutes} daq</div>}
        </div>
        <div className="bg-slate-50 rounded-lg p-3">
          <div className="text-xs text-slate-500 mb-1">Ketdim</div>
          <div className="text-xl font-semibold">{att?.check_out_time ? new Date(att.check_out_time).toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" }) : "—"}</div>
          {att?.early_leave_minutes > 0 && <div className="text-xs text-amber-600 mt-1">Erta ketish: {att.early_leave_minutes} daq</div>}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          className="btn-success flex-1"
          disabled={hasCheckIn || status === "loading"}
          onClick={() => doCheck("check-in")}>
          🟢 Keldim
        </button>
        <button
          className="btn-danger flex-1"
          disabled={!hasCheckIn || hasCheckOut || status === "loading"}
          onClick={() => doCheck("check-out")}>
          🔴 Ketdim
        </button>
      </div>

      {msg && (
        <div className={`mt-4 rounded-lg px-3 py-2 text-sm ${
          status === "error" ? "bg-rose-50 text-rose-700 border border-rose-200"
          : status === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
          : "bg-blue-50 text-blue-700 border border-blue-200"
        }`}>{msg}</div>
      )}

      <div className="mt-4 text-xs text-slate-500 flex items-center gap-2">
        <span>📍</span>
        <span>GPS + ofis Wi-Fi tekshiriladi. Ofis hududidan tashqari yoki boshqa tarmoqdan check-in qabul qilinmaydi.</span>
      </div>
    </div>
  );
}
