import React, { useState, useEffect } from "react";
import { Save, User, Bell, Shield, Sliders, CheckCircle2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { supabase } from "../supabaseClient";


const FATIGUE_THRESHOLDS = [
  { label: "Sensitive",   stressed: 25, fatigued: 50 },
  { label: "Normal",      stressed: 35, fatigued: 65 },
  { label: "Relaxed",     stressed: 45, fatigued: 75 },
];

const CAPTURE_RATES = [
  { label: "Low (1 fps)",      value: 1 },
  { label: "Normal (2 fps)",   value: 2 },
  { label: "High (5 fps)",     value: 5 },
];

function SettingSection({ title, icon: Icon, children, dark }) {
  return (
    <div className={`rounded-2xl border p-5 ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-indigo-600/20">
          <Icon size={16} className="text-indigo-400" />
        </div>
        <h3 className={`font-semibold text-sm ${dark ? "text-gray-200" : "text-gray-700"}`}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Toggle({ label, sub, checked, onChange, dark }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-inherit last:border-0">
      <div>
        <p className={`text-sm font-medium ${dark ? "text-gray-200" : "text-gray-700"}`}>{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative w-10 h-5.5 rounded-full transition-colors ${checked ? "bg-indigo-600" : dark ? "bg-gray-700" : "bg-gray-300"}`}
        style={{ width: 40, height: 22 }}
      >
        <span
          className="absolute top-0.5 left-0.5 w-4.5 h-4.5 bg-white rounded-full shadow transition-transform"
          style={{ width: 18, height: 18, transform: checked ? "translateX(18px)" : "translateX(0)" }}
        />
      </button>
    </div>
  );
}

export default function Settings() {
  const { user }   = useAuth();
  const { dark }   = useTheme();
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const [prefs, setPrefs] = useState({
    displayName:        "",
    captureRate:        2,
    thresholdPreset:    "Normal",
    notifyBrowser:      true,
    notifyOnStressed:   true,
    notifyOnFatigued:   true,
    breakReminderMins:  45,
    enableVoice:        false,
    enableTTS:          false,
    pomodoroMinutes:    25,
    showEARMAR:         true,
  });
  // Load from Supabase
  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    const loadPreferences = async () => {
      setLoading(true);

      const { data, error } = await supabase
        .from("profiles")
        .select("email, display_name, preferences")
        .eq("id", user.id)
        .maybeSingle();

      if (error) {
        console.error("Error loading settings:", error);
        setLoading(false);
        return;
      }

      if (data) {
        setPrefs(p => ({
          ...p,
          displayName: data.display_name || "",
          ...(data.preferences || {}),
        }));
      }

      setLoading(false);
    };

    loadPreferences();
  }, [user]);

  const set = (key, value) => setPrefs(p => ({ ...p, [key]: value }));

  const save = async () => {
    if (!user) return;

    setSaved(false);

    const { error } = await supabase
      .from("profiles")
      .upsert(
        {
          id: user.id,
          email: user.email,
          display_name: prefs.displayName,
          preferences: prefs,
          updated_at: new Date().toISOString(),
        },
        {
          onConflict: "id",
        }
      );

    if (error) {
      console.error("Error saving settings:", error);
      return;
    }

    setSaved(true);

    setTimeout(() => {
      setSaved(false);
    }, 2500);
  };

  if (loading) return <div className="p-6 text-gray-400 text-sm">Loading preferences…</div>;

  return (
    <div className={`p-4 md:p-6 min-h-full ${dark ? "text-white" : "text-gray-900"}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className={`text-sm mt-0.5 ${dark ? "text-gray-400" : "text-gray-500"}`}>
            Personalise your tracking experience
          </p>
        </div>
        <button onClick={save}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors
            ${saved ? "bg-emerald-600 text-white" : "bg-indigo-600 hover:bg-indigo-700 text-white"}`}>
          {saved ? <CheckCircle2 size={16} /> : <Save size={16} />}
          {saved ? "Saved!" : "Save Changes"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Profile */}
        <SettingSection title="Profile" icon={User} dark={dark}>
          <div className="space-y-3">
            <div>
              <label className={`block text-xs font-medium mb-1.5 ${dark ? "text-gray-400" : "text-gray-500"}`}>Email</label>
              <input type="email" value={user?.email || ""} disabled
                className={`w-full px-3 py-2 rounded-lg text-sm border opacity-60 cursor-not-allowed ${dark ? "bg-gray-800 border-gray-700 text-gray-300" : "bg-gray-50 border-gray-200 text-gray-600"}`}
              />
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1.5 ${dark ? "text-gray-400" : "text-gray-500"}`}>Display Name</label>
              <input type="text" value={prefs.displayName} onChange={e => set("displayName", e.target.value)}
                placeholder="Your name"
                className={`w-full px-3 py-2 rounded-lg text-sm border focus:outline-none focus:border-indigo-500 transition-colors ${dark ? "bg-gray-800 border-gray-700 text-white placeholder-gray-500" : "bg-white border-gray-200 text-gray-900 placeholder-gray-400"}`}
              />
            </div>
          </div>
        </SettingSection>

        {/* Detection */}
        <SettingSection title="Detection Settings" icon={Sliders} dark={dark}>
          <div className="space-y-4">
            <div>
              <label className={`block text-xs font-medium mb-2 ${dark ? "text-gray-400" : "text-gray-500"}`}>Sensitivity Preset</label>
              <div className="grid grid-cols-3 gap-2">
                {FATIGUE_THRESHOLDS.map(t => (
                  <button key={t.label}
                    onClick={() => set("thresholdPreset", t.label)}
                    className={`py-2 rounded-lg text-xs font-medium border transition-colors
                      ${prefs.thresholdPreset === t.label
                        ? "bg-indigo-600 border-indigo-600 text-white"
                        : dark ? "border-gray-700 text-gray-300 hover:bg-gray-800" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}>
                    {t.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {FATIGUE_THRESHOLDS.find(t => t.label === prefs.thresholdPreset)?.label === "Sensitive"
                  ? "Alerts at lower scores — good for high-focus work"
                  : prefs.thresholdPreset === "Relaxed"
                    ? "Alerts only at higher scores — good for light tasks"
                    : "Balanced thresholds for most work types"}
              </p>
            </div>

            <div>
              <label className={`block text-xs font-medium mb-2 ${dark ? "text-gray-400" : "text-gray-500"}`}>Capture Rate</label>
              <select value={prefs.captureRate} onChange={e => set("captureRate", Number(e.target.value))}
                className={`w-full px-3 py-2 rounded-lg text-sm border focus:outline-none focus:border-indigo-500 ${dark ? "bg-gray-800 border-gray-700 text-white" : "bg-white border-gray-200 text-gray-900"}`}>
                {CAPTURE_RATES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>

            <div>
              <label className={`block text-xs font-medium mb-2 ${dark ? "text-gray-400" : "text-gray-500"}`}>
                Break Reminder Every {prefs.breakReminderMins} min
              </label>
              <input type="range" min={20} max={90} step={5} value={prefs.breakReminderMins}
                onChange={e => set("breakReminderMins", Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>20 min</span><span>90 min</span>
              </div>
            </div>
          </div>
        </SettingSection>

        {/* Notifications */}
        <SettingSection title="Notifications" icon={Bell} dark={dark}>
          <div className="divide-y divide-inherit">
            <Toggle label="Browser notifications" sub="Requires permission" checked={prefs.notifyBrowser} onChange={v => set("notifyBrowser", v)} dark={dark} />
            <Toggle label="Alert on Stressed state" sub="Score ≥ 35" checked={prefs.notifyOnStressed} onChange={v => set("notifyOnStressed", v)} dark={dark} />
            <Toggle label="Alert on Fatigued state" sub="Score ≥ 65" checked={prefs.notifyOnFatigued} onChange={v => set("notifyOnFatigued", v)} dark={dark} />
          </div>
        </SettingSection>

        {/* Accessibility & UI */}
        <SettingSection title="Accessibility & UI" icon={Shield} dark={dark}>
          <div className="divide-y divide-inherit">
            <Toggle label="Voice input in chatbot" sub="Web Speech API" checked={prefs.enableVoice} onChange={v => set("enableVoice", v)} dark={dark} />
            <Toggle label="Text-to-speech responses" sub="Read chatbot replies aloud" checked={prefs.enableTTS} onChange={v => set("enableTTS", v)} dark={dark} />
            <Toggle label="Show EAR / MAR values" sub="Display raw facial metrics" checked={prefs.showEARMAR} onChange={v => set("showEARMAR", v)} dark={dark} />
          </div>
          <div className="mt-4">
            <label className={`block text-xs font-medium mb-2 ${dark ? "text-gray-400" : "text-gray-500"}`}>
              Pomodoro Focus Length: {prefs.pomodoroMinutes} min
            </label>
            <input type="range" min={15} max={60} step={5} value={prefs.pomodoroMinutes}
              onChange={e => set("pomodoroMinutes", Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>15 min</span><span>60 min</span>
            </div>
          </div>
        </SettingSection>
      </div>

      {/* Privacy note */}
      <div className={`mt-4 flex items-start gap-3 p-4 rounded-xl border text-xs ${dark ? "bg-gray-900/50 border-gray-800 text-gray-400" : "bg-gray-50 border-gray-200 text-gray-500"}`}>
        <Shield size={14} className="text-emerald-500 shrink-0 mt-0.5" />
        <span>
          Mentora processes all video locally in your browser. No camera footage is transmitted or stored.
          Only numeric metrics (fatigue score, EAR, MAR) are sent to the server and saved in your private account data.
        </span>
      </div>
    </div>
  );
}



