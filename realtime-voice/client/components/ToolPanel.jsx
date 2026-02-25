import { useEffect, useState } from "react";

const WMO_CODES = {
  0: "快晴", 1: "ほぼ晴れ", 2: "一部曇り", 3: "曇り",
  45: "霧", 48: "霧氷",
  51: "霧雨（弱）", 53: "霧雨", 55: "霧雨（強）",
  61: "小雨", 63: "雨", 65: "大雨",
  71: "小雪", 73: "雪", 75: "大雪",
  80: "にわか雨（弱）", 81: "にわか雨", 82: "にわか雨（強）",
  95: "雷雨", 96: "雷雨（雹あり）", 99: "激しい雷雨",
};

const sessionUpdate = {
  type: "session.update",
  session: {
    type: "realtime",
    tools: [
      {
        type: "function",
        name: "get_weather",
        description: "指定した都市の現在の天気と3日間の予報を取得する。ユーザーが天気を聞いた時に呼ぶ。",
        parameters: {
          type: "object",
          strict: true,
          properties: {
            city: {
              type: "string",
              description: "都市名（英語のローマ字表記。例: Tokyo, Osaka, Sapporo, Fukuoka, Naha）",
            },
          },
          required: ["city"],
        },
      },
    ],
    tool_choice: "auto",
  },
};

async function fetchWeather(city) {
  const geoRes = await fetch(
    `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=ja`
  );
  const geoData = await geoRes.json();
  if (!geoData.results?.length) throw new Error(`都市が見つかりません: ${city}`);

  const { latitude, longitude, name, admin1 } = geoData.results[0];

  const weatherRes = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
    `&current=temperature_2m,weathercode,windspeed_10m,precipitation` +
    `&daily=temperature_2m_max,temperature_2m_min,weathercode` +
    `&timezone=Asia%2FTokyo&forecast_days=3`
  );
  const w = await weatherRes.json();

  return {
    location: `${name}${admin1 ? `（${admin1}）` : ""}`,
    current: {
      temperature: w.current.temperature_2m,
      condition: WMO_CODES[w.current.weathercode] ?? "不明",
      windspeed: w.current.windspeed_10m,
      precipitation: w.current.precipitation,
    },
    forecast: w.daily.time.map((date, i) => ({
      date,
      max: w.daily.temperature_2m_max[i],
      min: w.daily.temperature_2m_min[i],
      condition: WMO_CODES[w.daily.weathercode[i]] ?? "不明",
    })),
  };
}

function WeatherDisplay({ result }) {
  const { location, current, forecast } = result;
  return (
    <div className="flex flex-col gap-3 mt-2">
      <div className="bg-blue-50 rounded-lg p-3">
        <div className="font-bold text-blue-800 text-sm">{location}</div>
        <div className="text-4xl font-bold mt-1">{current.temperature}°C</div>
        <div className="text-gray-600 mt-1">{current.condition}</div>
        <div className="text-xs text-gray-400 mt-1">
          風速 {current.windspeed} km/h　降水量 {current.precipitation} mm
        </div>
      </div>
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">3日間予報</div>
      {forecast.map((day) => (
        <div key={day.date} className="flex items-center justify-between bg-white border border-gray-100 rounded-lg px-3 py-2">
          <span className="text-sm text-gray-500">{day.date.slice(5).replace("-", "/")}</span>
          <span className="text-sm text-gray-600">{day.condition}</span>
          <span className="text-sm font-medium">
            <span className="text-red-500">{day.max}°</span>
            <span className="text-gray-300 mx-1">/</span>
            <span className="text-blue-500">{day.min}°</span>
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ToolPanel({ isSessionActive, sendClientEvent, events }) {
  const [functionAdded, setFunctionAdded] = useState(false);
  const [weatherResult, setWeatherResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!events || events.length === 0) return;

    const firstEvent = events[events.length - 1];
    if (!functionAdded && firstEvent.type === "session.created") {
      sendClientEvent(sessionUpdate);
      setFunctionAdded(true);
    }

    const mostRecentEvent = events[0];
    if (mostRecentEvent.type === "response.done" && mostRecentEvent.response?.output) {
      mostRecentEvent.response.output.forEach((output) => {
        if (output.type === "function_call" && output.name === "get_weather") {
          const { city } = JSON.parse(output.arguments);
          setLoading(true);
          setError(null);

          fetchWeather(city)
            .then((result) => {
              setWeatherResult(result);
              setLoading(false);
              sendClientEvent({
                type: "conversation.item.create",
                item: {
                  type: "function_call_output",
                  call_id: output.call_id,
                  output: JSON.stringify(result),
                },
              });
              sendClientEvent({ type: "response.create" });
            })
            .catch((err) => {
              setLoading(false);
              setError(err.message);
              sendClientEvent({
                type: "conversation.item.create",
                item: {
                  type: "function_call_output",
                  call_id: output.call_id,
                  output: JSON.stringify({ error: err.message }),
                },
              });
              sendClientEvent({ type: "response.create" });
            });
        }
      });
    }
  }, [events]);

  useEffect(() => {
    if (!isSessionActive) {
      setFunctionAdded(false);
      setWeatherResult(null);
      setError(null);
    }
  }, [isSessionActive]);

  return (
    <section className="h-full w-full flex flex-col gap-4">
      <div className="h-full bg-gray-50 rounded-md p-4">
        <h2 className="text-lg font-bold">天気予報</h2>
        {isSessionActive ? (
          loading ? (
            <p className="text-sm text-gray-500 mt-2">取得中...</p>
          ) : error ? (
            <p className="text-sm text-red-500 mt-2">{error}</p>
          ) : weatherResult ? (
            <WeatherDisplay result={weatherResult} />
          ) : (
            <p className="text-sm text-gray-500 mt-2">「東京の天気を教えて」と話しかけてみてください</p>
          )
        ) : (
          <p className="text-sm text-gray-400 mt-2">セッションを開始してください</p>
        )}
      </div>
    </section>
  );
}
