import React, { useState, useEffect } from "react";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Download, TrendingUp, Clock, Zap, Loader2 } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useSessionHistory } from "../hooks/useSessionHistory";
import api from "../utils/api";

const SC = { Normal: "#10b981", Stressed: "#f59e0b", Fatigued: "#ef4444" };

export default function Reports() {
  const { dark } = useTheme();
  const { sessions } = useSessionHistory(50);
  const [weekly, setWeekly] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    api.get("/api/v1/reports/weekly").then(r => setWeekly(r.data?.days || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selected) { setDetail(null); return; }
    api.get(`/api/v1/report?session_id=${selected}&format=json`).then(r => setDetail(r.data)).catch(() => {});
  }, [selected]);

  const exportPDF = async (id) => {
    setExporting(true);
    try {
      const res = await api.get(`/api/v1/report?session_id=${id}&format=pdf`, { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      Object.assign(document.createElement("a"), { href: url, download: `mentora_${id.slice(0,8)}.pdf` }).click();
      URL.revokeObjectURL(url);
    } finally { setExporting(false); }
  };

  const totalMins  = weekly.reduce((a, d) => a + (d.total_time_min || 0), 0);
  const avgFatigue = weekly.length ? Math.round(weekly.reduce((a, d) => a + d.avg_fatigue, 0) / weekly.length) : 0;
  const totalSess  = weekly.reduce((a, d) => a + (d.sessions || 0), 0);
  const pieData    = [
    { name: "Normal",   value: weekly.filter(d => d.avg_fatigue < 35).length },
    { name: "Stressed", value: weekly.filter(d => d.avg_fatigue >= 35 && d.avg_fatigue < 65).length },
    { name: "Fatigued", value: weekly.filter(d => d.avg_fatigue >= 65).length },
  ].filter(d => d.value > 0);

  const tt = {
    contentStyle: { background: dark ? "#1e293b" : "#fff", border: "1px solid #334155", borderRadius: 8 },
    labelStyle: { color: "#94a3b8" },
  };

  const an = detail?.analytics;

  return (
    <div className={`p-4 md:p-6 min-h-full ${dark ? "text-white" : "text-gray-900"}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Reports & Analytics</h1>
          <p className={`text-sm mt-0.5 ${dark ? "text-gray-400" : "text-gray-500"}`}>Last 7 days</p>
        </div>
        {selected && (
          <button onClick={() => exportPDF(selected)} disabled={exporting}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-semibold transition-colors">
            {exporting ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />}
            {exporting ? "Generating…" : "Export PDF"}
          </button>
        )}
      </div>

      {sessions.length > 0 && (
        <div className="mb-5">
          <label className={`block text-xs font-semibold mb-2 ${dark ? "text-gray-400" : "text-gray-500"}`}>DRILL INTO A SESSION</label>
          <select value={selected || ""} onChange={e => setSelected(e.target.value || null)}
            className={`w-full md:w-80 px-3 py-2.5 rounded-xl text-sm border focus:outline-none focus:border-indigo-500 ${dark ? "bg-gray-800 border-gray-700 text-white" : "bg-white border-gray-200 text-gray-900"}`}>
            <option value="">— Weekly overview —</option>
            {sessions.slice(0, 30).map(s => {
              const d = new Date(s.started_at * 1000);
              return <option key={s.session_id} value={s.session_id}>{d.toLocaleDateString()} {d.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})} · avg {s.avg_fatigue ?? "?"}/100</option>;
            })}
          </select>
        </div>
      )}

      {selected && an && (
        <div className="space-y-4 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Avg fatigue", value: `${an.avg_fatigue_score}/100`, color: an.avg_fatigue_score >= 65 ? "#ef4444" : an.avg_fatigue_score >= 35 ? "#f59e0b" : "#10b981" },
              { label: "Peak fatigue", value: `${an.peak_fatigue_score}/100`, color: "#6C63FF" },
              { label: "Duration", value: `${an.duration_minutes} min`, color: "#22d3ee" },
              { label: "Frames", value: an.total_frames, color: "#10b981" },
            ].map(({ label, value, color }) => (
              <div key={label} className={`rounded-2xl p-4 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
                <p className={`text-xs mb-1 ${dark ? "text-gray-400" : "text-gray-500"}`}>{label}</p>
                <p className="text-xl font-bold" style={{ color }}>{value}</p>
              </div>
            ))}
          </div>
          {detail.timeline?.length > 0 && (
            <div className={`rounded-2xl p-5 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
              <h3 className={`text-sm font-semibold mb-4 ${dark ? "text-gray-300" : "text-gray-600"}`}>Session timeline</h3>
              <ResponsiveContainer width="100%" height={150}>
                <LineChart data={detail.timeline}>
                  <XAxis dataKey="t" tickFormatter={v => new Date(v*1000).toLocaleTimeString([],{minute:"2-digit",second:"2-digit"})} tick={{fontSize:10,fill:"#94a3b8"}} interval="preserveStartEnd" />
                  <YAxis domain={[0,100]} tick={{fontSize:10,fill:"#94a3b8"}} width={28} />
                  <Tooltip {...tt} formatter={v => [`${v}/100`, "Fatigue"]} />
                  <Line type="monotone" dataKey="score" stroke="#6C63FF" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className={`rounded-2xl p-5 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
            <h3 className={`text-sm font-semibold mb-3 ${dark ? "text-gray-300" : "text-gray-600"}`}>Time in each state</h3>
            <div className="space-y-2">
              {Object.entries(an.state_distribution || {}).map(([st, count]) => {
                const pct = Math.round((count / an.total_frames) * 100) || 0;
                return (
                  <div key={st} className="flex items-center gap-3">
                    <span className={`text-xs w-16 ${dark ? "text-gray-400" : "text-gray-500"}`}>{st}</span>
                    <div className={`flex-1 h-2 rounded-full ${dark ? "bg-gray-700" : "bg-gray-200"}`}>
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: SC[st] || "#6b7280" }} />
                    </div>
                    <span className="text-xs font-mono w-8 text-right" style={{ color: SC[st] || "#6b7280" }}>{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {!selected && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-5">
            {[
              {icon: Clock, label:"Total focus time", value:`${Math.round(totalMins)} min`, color:"#6C63FF"},
              {icon: TrendingUp, label:"Avg fatigue score", value:`${avgFatigue}/100`, color: avgFatigue>=65?"#ef4444":avgFatigue>=35?"#f59e0b":"#10b981"},
              {icon: Zap, label:"Sessions this week", value:totalSess, color:"#10b981"},
            ].map(({icon:Icon, label, value, color}) => (
              <div key={label} className={`rounded-2xl p-4 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={13} style={{color}} />
                  <span className={`text-xs ${dark?"text-gray-400":"text-gray-500"}`}>{label}</span>
                </div>
                <p className="text-2xl font-bold" style={{color}}>{value}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className={`rounded-2xl p-5 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
              <h3 className={`text-sm font-semibold mb-4 ${dark?"text-gray-300":"text-gray-600"}`}>Daily avg fatigue</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={weekly}>
                  <XAxis dataKey="date" tickFormatter={d=>d?.slice(5)} tick={{fontSize:11,fill:"#94a3b8"}} />
                  <YAxis domain={[0,100]} tick={{fontSize:11,fill:"#94a3b8"}} width={28} />
                  <Tooltip {...tt} />
                  <Bar dataKey="avg_fatigue" radius={[4,4,0,0]}>
                    {weekly.map((d,i) => <Cell key={i} fill={d.avg_fatigue>=65?"#ef4444":d.avg_fatigue>=35?"#f59e0b":"#10b981"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className={`rounded-2xl p-5 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
              <h3 className={`text-sm font-semibold mb-4 ${dark?"text-gray-300":"text-gray-600"}`}>Daily focus time (min)</h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={weekly}>
                  <XAxis dataKey="date" tickFormatter={d=>d?.slice(5)} tick={{fontSize:11,fill:"#94a3b8"}} />
                  <YAxis tick={{fontSize:11,fill:"#94a3b8"}} width={32} />
                  <Tooltip {...tt} />
                  <Line type="monotone" dataKey="total_time_min" stroke="#6C63FF" strokeWidth={2} dot={{r:4,fill:"#6C63FF"}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`rounded-2xl p-5 border ${dark?"bg-gray-900 border-gray-800":"bg-white border-gray-200"} shadow-sm flex flex-col items-center`}>
              <h3 className={`text-sm font-semibold mb-4 self-start ${dark?"text-gray-300":"text-gray-600"}`}>State distribution</h3>
              {pieData.length > 0 ? (
                <>
                  <PieChart width={160} height={160}>
                    <Pie data={pieData} cx={75} cy={75} innerRadius={45} outerRadius={70} dataKey="value">
                      {pieData.map((e,i) => <Cell key={i} fill={SC[e.name]} />)}
                    </Pie>
                  </PieChart>
                  <div className="mt-3 space-y-1">
                    {pieData.map(d => (
                      <div key={d.name} className="flex items-center gap-2 text-xs">
                        <div className="w-2.5 h-2.5 rounded-full" style={{background:SC[d.name]}} />
                        <span className={dark?"text-gray-300":"text-gray-600"}>{d.name}</span>
                        <span className="font-mono ml-auto text-gray-400">{d.value}d</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : <p className="text-sm text-gray-400 mt-8">No data yet</p>}
            </div>
            <div className={`md:col-span-2 rounded-2xl border overflow-hidden ${dark?"bg-gray-900 border-gray-800":"bg-white border-gray-200"} shadow-sm`}>
              <div className={`px-5 py-3 border-b ${dark?"border-gray-800":"border-gray-200"}`}>
                <h3 className={`text-sm font-semibold ${dark?"text-gray-300":"text-gray-600"}`}>Day-by-day summary</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className={dark?"bg-gray-800/50":"bg-gray-50"}>
                      {["Date","Sessions","Avg Score","Focus Time","Status"].map(h => (
                        <th key={h} className={`px-4 py-2.5 text-left text-xs font-medium ${dark?"text-gray-400":"text-gray-500"}`}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {weekly.length === 0 ? (
                      <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">No sessions yet.</td></tr>
                    ) : weekly.map((d,i) => (
                      <tr key={d.date} className={`border-t ${dark?"border-gray-800":"border-gray-100"} ${i%2?dark?"bg-gray-800/20":"bg-gray-50/50":""}`}>
                        <td className={`px-4 py-2.5 font-mono text-xs ${dark?"text-gray-300":"text-gray-700"}`}>{d.date}</td>
                        <td className={`px-4 py-2.5 ${dark?"text-gray-300":"text-gray-700"}`}>{d.sessions}</td>
                        <td className="px-4 py-2.5 font-bold" style={{color:d.avg_fatigue>=65?"#ef4444":d.avg_fatigue>=35?"#f59e0b":"#10b981"}}>{d.avg_fatigue}</td>
                        <td className={`px-4 py-2.5 ${dark?"text-gray-300":"text-gray-700"}`}>{d.total_time_min} min</td>
                        <td className="px-4 py-2.5">
                          <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{background:(d.avg_fatigue>=65?"#ef4444":d.avg_fatigue>=35?"#f59e0b":"#10b981")+"22",color:d.avg_fatigue>=65?"#ef4444":d.avg_fatigue>=35?"#f59e0b":"#10b981"}}>
                            {d.avg_fatigue>=65?"Fatigued":d.avg_fatigue>=35?"Stressed":"Normal"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
