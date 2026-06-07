import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  MessageSquareText,
  RefreshCcw,
  Search,
  ThumbsUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Label,
} from "recharts";

const COLORS = {
  positive: "#16a34a",
  negative: "#dc2626",
  neutral: "#64748b",
  unclassified: "#9333ea",
};

const formatNumber = (value) => new Intl.NumberFormat("en-US").format(value ?? 0);
const formatPercent = (value) => `${((value ?? 0) * 100).toFixed(1)}%`;
const TRACKED_VIDEO_TITLE = "#3 KNICKS at #2 SPURS | NBA FINALS GAME 1 HIGHLIGHTS | June 3, 2026";

function useDashboardData() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/data/dashboard-data.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Dashboard data was not found");
        }
        return response.json();
      })
      .then(setData)
      .catch(setError);
  }, []);

  return { data, error };
}

function KpiCard({ icon: Icon, label, value, detail, tone = "default" }) {
  return (
    <section className={`kpi-card ${tone}`}>
      <div className="kpi-icon" aria-hidden="true">
        <Icon size={18} />
      </div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
    </section>
  );
}

function Panel({ title, action, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        {action ? <span>{action}</span> : null}
      </div>
      {children}
    </section>
  );
}

function renderPieLabel({ name, percent }) {
  return `${name}: ${(percent * 100).toFixed(1)}%`;
}

function SentimentPie({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart margin={{ top: 24, right: 42, bottom: 24, left: 42 }}>
        <Pie
          data={data}
          dataKey="count"
          nameKey="label"
          innerRadius={64}
          outerRadius={100}
          paddingAngle={3}
          label={renderPieLabel}
          labelLine
        >
          {data.map((entry) => (
            <Cell key={entry.label} fill={COLORS[entry.label] ?? COLORS.unclassified} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => formatNumber(value)} />
      </PieChart>
    </ResponsiveContainer>
  );
}

function SentimentBars({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 36, left: 44 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label">
          <Label value="Sentiment Label" offset={-24} position="insideBottom" />
        </XAxis>
        <YAxis>
          <Label value="Comment Count" angle={-90} position="insideLeft" offset={-30} />
        </YAxis>
        <Tooltip formatter={(value) => formatNumber(value)} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={COLORS[entry.label] ?? COLORS.unclassified} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function ModelComparison({ rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Type</th>
            <th>Accuracy</th>
            <th>Macro F1</th>
            <th>Weighted F1</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.model}>
              <td>{row.model}</td>
              <td>{row.type}</td>
              <td>{formatPercent(row.accuracy)}</td>
              <td>{formatPercent(row.macroF1)}</td>
              <td>{formatPercent(row.weightedF1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function KeywordCloud({ groups }) {
  return (
    <div className="keyword-grid">
      {Object.entries(groups).map(([sentiment, terms]) => (
        <div className="keyword-block" key={sentiment}>
          <h3>{sentiment}</h3>
          <div className="keywords">
            {terms.slice(0, 12).map((item) => (
              <span key={`${sentiment}-${item.term}`}>{item.term} <b>{item.count}</b></span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function TopComments({ comments }) {
  return (
    <div className="comment-list">
      {comments.map((comment, index) => (
        <article className="comment-row" key={`${comment.author}-${index}`}>
          <div>
            <div className="comment-meta">
              <strong>{comment.author || "Unknown"}</strong>
              <span className={`pill ${comment.sentiment}`}>{comment.sentiment}</span>
            </div>
            <p>{comment.text}</p>
          </div>
          <div className="comment-stats">
            <span>{formatNumber(comment.likes)} likes</span>
            <span>{formatNumber(comment.replies)} replies</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function TimeSeries({ rows }) {
  if (!rows.length) {
    return <p className="empty-state">No valid timestamp data available.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={rows} margin={{ top: 12, right: 18, bottom: 38, left: 44 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" minTickGap={28}>
          <Label value="Date" offset={-26} position="insideBottom" />
        </XAxis>
        <YAxis>
          <Label value="Comment Count" angle={-90} position="insideLeft" offset={-30} />
        </YAxis>
        <Tooltip />
        <Line type="monotone" dataKey="positive" stroke={COLORS.positive} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="negative" stroke={COLORS.negative} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="neutral" stroke={COLORS.neutral} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function App() {
  const { data, error } = useDashboardData();

  const bestModel = useMemo(() => {
    if (!data?.modelComparison?.length) return null;
    return data.modelComparison[0];
  }, [data]);

  if (error) {
    return (
      <main className="app-shell centered">
        <p>{error.message}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="app-shell centered">
        <RefreshCcw className="spin" size={24} />
        <p>Loading dashboard data...</p>
      </main>
    );
  }

  const overview = data.overview;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>NBA YouTube Comment Analytics</h1>
          <p className="lede">
            A reusable dashboard that starts from the YouTube Data API, stores and transforms the data in PostgreSQL, and tracks comment volume, sentiment model behavior, and audience signals from the analytics pipeline.
          </p>
        </div>
        <div className="source-box">
          <span>Tracked video</span>
          <strong>{TRACKED_VIDEO_TITLE}</strong>
          <small>{overview.videoIds?.[0] ?? "N/A"}</small>
        </div>
      </header>

      <section className="kpi-grid">
        <KpiCard icon={MessageSquareText} label="Comments" value={formatNumber(overview.totalComments)} detail={`${formatNumber(overview.usableComments)} usable after filtering`} />
        <KpiCard icon={ThumbsUp} label="Comment Likes" value={formatNumber(overview.totalLikesOnComments)} detail={`${formatNumber(overview.totalRepliesOnThreads)} replies in threads`} tone="green" />
        <KpiCard icon={BrainCircuit} label="Best Model" value={overview.bestModel} detail={`${formatNumber(overview.trainingRowsUsed)} manual labels used`} tone="blue" />
        <KpiCard icon={Activity} label="Avg Length" value={`${overview.avgCommentLength} chars`} detail={`${formatNumber(overview.lowInformationComments)} low-information comments`} tone="amber" />
      </section>

      <section className="dashboard-grid two-columns">
        <Panel title="Supervised Sentiment" action="Linear SVM prediction output">
          <SentimentPie data={data.sentimentDistribution} />
          <div className="legend-row">
            {data.sentimentDistribution.map((item) => (
              <span key={item.label}><i style={{ background: COLORS[item.label] }} />{item.label}: {formatNumber(item.count)}</span>
            ))}
          </div>
        </Panel>

        <Panel title="Lexicon Baseline" action="Rule-based comparison">
          <SentimentBars data={data.lexiconDistribution} />
        </Panel>
      </section>

      <section className="dashboard-grid wide-left">
        <Panel title="Model Comparison" action={bestModel ? `Best macro F1: ${bestModel.model}` : ""}>
          <ModelComparison rows={data.modelComparison} />
        </Panel>

        <Panel title="Sentiment Quality Notes">
          <div className="insight-list">
            <p><BarChart3 size={16} /> Linear SVM currently leads on macro F1 and overall accuracy.</p>
            <p><Search size={16} /> Lexicon labeling is useful as a baseline, but it over-predicts neutral comments.</p>
            <p><BrainCircuit size={16} /> Neutral remains the hardest class because the manual sample has fewer neutral labels.</p>
          </div>
        </Panel>
      </section>

      <section className="dashboard-grid two-columns">
        <Panel title="Comment Activity Over Time">
          <TimeSeries rows={data.commentsOverTime} />
        </Panel>

        <Panel title="Average Comment Behavior">
          <div className="table-wrap compact">
            <table>
              <thead>
                <tr>
                  <th>Sentiment</th>
                  <th>Comments</th>
                  <th>Avg Length</th>
                  <th>Avg Likes</th>
                </tr>
              </thead>
              <tbody>
                {data.lengthBySentiment.map((row) => (
                  <tr key={row.label}>
                    <td><span className={`pill ${row.label}`}>{row.label}</span></td>
                    <td>{formatNumber(row.comments)}</td>
                    <td>{row.avgLength}</td>
                    <td>{row.avgLikes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <Panel title="Top Keywords By Sentiment">
        <KeywordCloud groups={data.keywordsBySentiment} />
      </Panel>

      <Panel title="Most Engaged Comments">
        <TopComments comments={data.topComments.overall} />
      </Panel>
    </main>
  );
}

export default App;



