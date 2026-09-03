import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  GitBranch,
  Gauge,
  ShieldAlert,
  Sparkles,
  TestTube2,
  TrendingUp,
  Wrench,
  Clock3,
  XCircle,
  Zap,
  ShieldCheck,
  Activity,
  Timer,
} from "lucide-react";

import { SelfHealingProfile } from "@/types";

type SelfHealingProfileWithStatus = SelfHealingProfile & {
  verification_status?: string | null;
  verification_reason?: string | null;
};

export default function SelfHealingPanel({
  selfHealing,
}: {
  selfHealing?: SelfHealingProfile;
}) {
  if (!selfHealing) return null;

  const profile =
    selfHealing as SelfHealingProfileWithStatus;

  const riskMax = 100;

  // =========================================================
  // VERIFICATION STATE
  // =========================================================
  //
  // Backend is now authoritative:
  //
  // verification_status:
  //   verified / passed -> VERIFIED
  //   failed            -> FAILED
  //   pending           -> PENDING
  //
  // Legacy fallback:
  //   verification_passed === true  -> VERIFIED
  //   verification_passed === false -> FAILED
  //   verification_passed === null  -> PENDING
  //
  // IMPORTANT:
  // `false` is now treated as FAILED because the backend
  // explicitly uses false for an actual failed verification.
  // =========================================================

  const verificationStatusValue =
    typeof profile.verification_status === "string"
      ? profile.verification_status.trim().toLowerCase()
      : undefined;

  const verificationPassed =
    profile.verification_passed;

  const isVerified =
    verificationStatusValue === "passed" ||
    verificationStatusValue === "verified" ||
    (
      verificationStatusValue === undefined &&
      verificationPassed === true
    );

  const isFailed =
    verificationStatusValue === "failed" ||
    (
      verificationStatusValue === undefined &&
      verificationPassed === false
    );

  const isPending =
    !isVerified && !isFailed;

  const verificationStatus = isVerified
    ? {
        label: "Verified",
        headerLabel: "Verification verified",
        icon: (
          <CheckCircle2 className="w-4 h-4 shrink-0" />
        ),
        textClass: "text-emerald-200",
        borderClass: "border-emerald-500/30",
        bgClass: "bg-emerald-500/10",
        cardTextClass: "text-emerald-300",
      }
    : isFailed
      ? {
          label: "Failed",
          headerLabel: "Verification failed",
          icon: (
            <XCircle className="w-4 h-4 shrink-0" />
          ),
          textClass: "text-rose-200",
          borderClass: "border-rose-500/30",
          bgClass: "bg-rose-500/10",
          cardTextClass: "text-rose-300",
        }
      : {
          label: "Pending",
          headerLabel: "Verification pending",
          icon: (
            <Clock3 className="w-4 h-4 shrink-0" />
          ),
          textClass: "text-amber-200",
          borderClass: "border-amber-500/30",
          bgClass: "bg-amber-500/10",
          cardTextClass: "text-amber-300",
        };

  // =========================================================
  // HEALTH TREND
  // =========================================================

  const healthTrend = Array.isArray(
    selfHealing.health_trend
  )
    ? selfHealing.health_trend
        .map((point) => {
          const value =
            typeof point === "number" &&
            Number.isFinite(point)
              ? point
              : Number(point);

          if (!Number.isFinite(value)) {
            return 0;
          }

          return Math.max(
            0,
            Math.min(100, value)
          );
        })
        .slice(0, 5)
    : [];

  // =========================================================
  // SAFE NUMERIC HELPERS
  // =========================================================

  const confidence = Number(
    selfHealing.confidence ?? 0
  );

  const fixesGenerated = Number(
    selfHealing.fixes_generated ?? 0
  );

  const testsCreated = Number(
    selfHealing.tests_created ?? 0
  );

  const prReviewScore = Number(
    selfHealing.pr_agent_review?.review_score ?? 0
  );

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <section
      className="
        w-full
        min-w-0
        overflow-hidden
        bg-slate-950/80
        border
        border-slate-800
        rounded-3xl
        p-4
        sm:p-6
        shadow-[0_0_50px_-18px_rgba(96,165,250,0.55)]
      "
    >
      {/* ===================================================== */}
      {/* HEADER                                                 */}
      {/* ===================================================== */}

      <div
        className="
          flex
          items-start
          justify-between
          gap-4
          flex-wrap
          mb-6
        "
      >
        <div className="min-w-0">
          <div
            className="
              inline-flex
              items-center
              gap-2
              px-2.5
              py-1
              rounded-full
              border
              border-cyan-500/30
              bg-cyan-500/10
              text-cyan-300
              text-[11px]
              font-bold
              uppercase
              tracking-[0.12em]
            "
          >
            <Sparkles className="w-3.5 h-3.5 shrink-0" />
            Self-Healing Auditor
          </div>

          <h2
            className="
              mt-3
              text-xl
              sm:text-2xl
              font-extrabold
              text-slate-50
              leading-tight
            "
          >
            Audit → Diagnose → Fix → Test → Verify
          </h2>
        </div>

        {/* =================================================== */}
        {/* VERIFICATION BADGE                                  */}
        {/* =================================================== */}

        <div
          className={`
            inline-flex
            min-w-0
            max-w-full
            shrink-0
            items-center
            justify-center
            gap-2
            rounded-2xl
            border
            px-3
            py-2
            text-sm
            whitespace-nowrap
            ${verificationStatus.borderClass}
            ${verificationStatus.bgClass}
            ${verificationStatus.textClass}
          `}
          title={
            profile.verification_reason ||
            verificationStatus.headerLabel
          }
        >
          {verificationStatus.icon}

          <span className="font-semibold truncate">
            {verificationStatus.headerLabel}
          </span>
        </div>
      </div>

      {/* ===================================================== */}
      {/* MAIN GRID                                              */}
      {/* ===================================================== */}

      <div
        className="
          grid
          grid-cols-1
          xl:grid-cols-[minmax(0,1.6fr)_minmax(280px,1fr)]
          gap-6
          min-w-0
        "
      >
        {/* =================================================== */}
        {/* LEFT SIDE                                            */}
        {/* =================================================== */}

        <div className="space-y-6 min-w-0">

          {/* ================================================= */}
          {/* SUMMARY CARDS                                     */}
          {/* ================================================= */}

          <div
            className="
              grid
              grid-cols-2
              sm:grid-cols-4
              gap-3
              sm:gap-4
              min-w-0
            "
          >

            {/* Confidence */}

            <div
              className="
                min-w-0
                rounded-2xl
                border
                border-slate-800
                bg-slate-900/80
                p-3
                sm:p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-2
                  text-cyan-300
                  text-xs
                  uppercase
                  tracking-wide
                "
              >
                <BrainCircuit className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">
                  Confidence
                </span>
              </div>

              <div
                className="
                  mt-3
                  text-2xl
                  sm:text-3xl
                  font-black
                  text-white
                  truncate
                "
              >
                {confidence.toFixed(1)}%
              </div>
            </div>

            {/* Fixes */}

            <div
              className="
                min-w-0
                rounded-2xl
                border
                border-slate-800
                bg-slate-900/80
                p-3
                sm:p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-2
                  text-violet-300
                  text-xs
                  uppercase
                  tracking-wide
                "
              >
                <Wrench className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">
                  Fixes
                </span>
              </div>

              <div
                className="
                  mt-3
                  text-2xl
                  sm:text-3xl
                  font-black
                  text-white
                  truncate
                "
              >
                {fixesGenerated}
              </div>
            </div>

            {/* Tests */}

            <div
              className="
                min-w-0
                rounded-2xl
                border
                border-slate-800
                bg-slate-900/80
                p-3
                sm:p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-2
                  text-amber-300
                  text-xs
                  uppercase
                  tracking-wide
                "
              >
                <TestTube2 className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">
                  Tests
                </span>
              </div>

              <div
                className="
                  mt-3
                  text-2xl
                  sm:text-3xl
                  font-black
                  text-white
                  truncate
                "
              >
                {testsCreated}
              </div>
            </div>

            {/* Verification */}

            <div
              className="
                min-w-0
                rounded-2xl
                border
                border-slate-800
                bg-slate-900/80
                p-3
                sm:p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-2
                  text-emerald-300
                  text-xs
                  uppercase
                  tracking-wide
                "
              >
                <ShieldAlert className="w-3.5 h-3.5 shrink-0" />

                <span className="truncate">
                  Verification
                </span>
              </div>

              <div
                className={`
                  mt-3
                  text-2xl
                  sm:text-3xl
                  font-black
                  leading-none
                  truncate
                  ${verificationStatus.cardTextClass}
                `}
              >
                {verificationStatus.label}
              </div>
            </div>
          </div>

          {/* ================================================= */}
          {/* AUTONOMOUS CONTROL LOOP                           */}
          {/* ================================================= */}

          <div
            className="
              rounded-2xl
              border
              border-slate-800
              bg-slate-900/80
              p-4
              sm:p-5
            "
          >
            <div
              className="
                flex
                items-center
                gap-2
                text-xs
                font-bold
                uppercase
                tracking-[0.12em]
                text-slate-300
              "
            >
              <Gauge className="w-4 h-4 text-cyan-400 shrink-0" />
              Autonomous control loop
            </div>

            <div className="mt-4 space-y-3">
              {(selfHealing.automated_steps ?? []).map(
                (step, index) => (
                  <div
                    key={`${step}-${index}`}
                    className="
                      flex
                      gap-3
                      items-start
                      min-w-0
                    "
                  >
                    <div
                      className="
                        mt-0.5
                        flex
                        h-6
                        w-6
                        shrink-0
                        items-center
                        justify-center
                        rounded-full
                        bg-cyan-500/15
                        text-[10px]
                        font-bold
                        text-cyan-300
                      "
                    >
                      {index + 1}
                    </div>

                    <p
                      className="
                        min-w-0
                        text-sm
                        text-slate-300
                        leading-relaxed
                      "
                    >
                      {step}
                    </p>
                  </div>
                )
              )}
            </div>
          </div>

          {/* ================================================= */}
          {/* PR AGENT REVIEW                                   */}
          {/* ================================================= */}

          <div
            className="
              rounded-2xl
              border
              border-slate-800
              bg-slate-900/80
              p-4
              sm:p-5
            "
          >
            <div
              className="
                flex
                items-center
                gap-2
                text-xs
                font-bold
                uppercase
                tracking-[0.12em]
                text-slate-300
              "
            >
              <Sparkles
                className="
                  w-4
                  h-4
                  text-cyan-400
                  shrink-0
                "
              />

              PR agent review
            </div>

            <p
              className="
                mt-3
                text-sm
                text-slate-300
                leading-relaxed
              "
            >
              {selfHealing.pr_agent_review?.summary ||
                "No PR agent review available yet."}
            </p>

            <div
              className="
                mt-4
                rounded-xl
                border
                border-emerald-500/30
                bg-emerald-500/10
                p-3
                text-xs
                text-emerald-200
              "
            >
              <div
                className="
                  font-semibold
                  uppercase
                  tracking-wide
                "
              >
                Suggested commit
              </div>

              <div
                className="
                  mt-1
                  font-mono
                  text-[11px]
                  break-words
                "
              >
                {selfHealing.pr_agent_review
                  ?.recommended_commit ||
                  "No recommendation available"}
              </div>
            </div>

            <div
              className="
                mt-4
                flex
                items-center
                justify-between
                gap-3
                text-xs
                text-slate-300
              "
            >
              <span>
                Review score
              </span>

              <span
                className="
                  shrink-0
                  font-bold
                  text-white
                "
              >
                {prReviewScore.toFixed(1)}
                /100
              </span>
            </div>
          </div>

          {/* ================================================= */}
          {/* HEALTH TREND                                      */}
          {/* ================================================= */}

          <div
            className="
              rounded-2xl
              border
              border-slate-800
              bg-slate-900/80
              p-4
              sm:p-5
              min-w-0
            "
          >
            <div
              className="
                flex
                items-center
                gap-2
                text-xs
                font-bold
                uppercase
                tracking-[0.12em]
                text-slate-300
              "
            >
              <TrendingUp className="w-4 h-4 text-violet-400 shrink-0" />
              Repository health trend
            </div>

            {healthTrend.length > 0 ? (
              <div className="mt-5 w-full min-w-0">
                <div
                  className="
                    relative
                    h-52
                    w-full
                    min-w-0
                    overflow-hidden
                    rounded-xl
                    bg-slate-950/40
                    border
                    border-slate-800/70
                  "
                >

                  {/* Grid */}

                  <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute left-10 right-3 top-[20%] border-t border-slate-800/70" />
                    <div className="absolute left-10 right-3 top-[40%] border-t border-slate-800/70" />
                    <div className="absolute left-10 right-3 top-[60%] border-t border-slate-800/70" />
                    <div className="absolute left-10 right-3 top-[80%] border-t border-slate-800/70" />
                  </div>

                  {/* Y axis */}

                  <div
                    className="
                      absolute
                      left-2
                      top-2
                      bottom-8
                      flex
                      flex-col
                      justify-between
                      text-[9px]
                      text-slate-500
                      pointer-events-none
                    "
                  >
                    <span>100</span>
                    <span>75</span>
                    <span>50</span>
                    <span>25</span>
                    <span>0</span>
                  </div>

                  {/* Chart */}

                  <svg
                    className="
                      absolute
                      inset-0
                      h-full
                      w-full
                    "
                    viewBox="0 0 640 200"
                    preserveAspectRatio="none"
                    role="img"
                    aria-label="Repository health trend chart"
                  >
                    <defs>
                      <linearGradient
                        id="healthBarGradient"
                        x1="0"
                        y1="1"
                        x2="0"
                        y2="0"
                      >
                        <stop
                          offset="0%"
                          stopColor="#06b6d4"
                          stopOpacity="0.85"
                        />

                        <stop
                          offset="100%"
                          stopColor="#8b5cf6"
                          stopOpacity="0.95"
                        />
                      </linearGradient>
                    </defs>

                    {healthTrend.map(
                      (value, index) => {
                        const count =
                          healthTrend.length;

                        /*
                         * Extra horizontal padding prevents
                         * the first/last Audit label from being
                         * clipped by the SVG viewport.
                         */

                        const chartLeft = 65;
                        const chartRight = 575;
                        const chartTop = 15;
                        const chartBottom = 158;

                        const chartWidth =
                          chartRight - chartLeft;

                        const chartHeight =
                          chartBottom - chartTop;

                        const x =
                          count === 1
                            ? chartLeft +
                              chartWidth / 2
                            : chartLeft +
                              (
                                index *
                                chartWidth
                              ) /
                                (count - 1);

                        const barWidth =
                          count === 1
                            ? 70
                            : Math.min(
                                64,
                                Math.max(
                                  24,
                                  chartWidth /
                                    count -
                                    18
                                )
                              );

                        const barHeight =
                          Math.max(
                            4,
                            (value / 100) *
                              chartHeight
                          );

                        const y =
                          chartBottom -
                          barHeight;

                        return (
                          <g
                            key={`health-point-${index}`}
                          >
                            <rect
                              x={
                                x -
                                barWidth / 2
                              }
                              y={y}
                              width={barWidth}
                              height={barHeight}
                              rx="8"
                              fill="url(#healthBarGradient)"
                            />

                            <text
                              x={x}
                              y={Math.max(
                                12,
                                y - 7
                              )}
                              textAnchor="middle"
                              fill="#e2e8f0"
                              fontSize="11"
                              fontWeight="700"
                            >
                              {Math.round(
                                value
                              )}
                              %
                            </text>

                            <text
                              x={x}
                              y="186"
                              textAnchor="middle"
                              fill="#94a3b8"
                              fontSize="9"
                              fontWeight="600"
                            >
                              Audit {index + 1}
                            </text>
                          </g>
                        );
                      }
                    )}
                  </svg>
                </div>
              </div>
            ) : (
              <div
                className="
                  mt-5
                  rounded-xl
                  border
                  border-slate-800
                  bg-slate-950/60
                  p-6
                  text-center
                "
              >
                <TrendingUp
                  className="
                    mx-auto
                    w-8
                    h-8
                    text-slate-600
                  "
                />

                <p
                  className="
                    mt-3
                    text-sm
                    font-semibold
                    text-slate-300
                  "
                >
                  No historical audit data yet
                </p>

                <p
                  className="
                    mt-1
                    text-xs
                    text-slate-500
                  "
                >
                  Run additional audits to
                  track repository health over
                  time.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* =================================================== */}
        {/* RIGHT SIDE                                           */}
        {/* =================================================== */}

        <div className="space-y-6 min-w-0">

          {/* ================================================= */}
          {/* PREDICTIVE RISK                                  */}
          {/* ================================================= */}

          <div
            className="
              rounded-2xl
              border
              border-slate-800
              bg-slate-900/80
              p-4
              sm:p-5
            "
          >
            <div
              className="
                flex
                items-center
                gap-2
                text-xs
                font-bold
                uppercase
                tracking-[0.12em]
                text-slate-300
              "
            >
              <ShieldAlert
                className="
                  w-4
                  h-4
                  text-rose-400
                  shrink-0
                "
              />

              Predictive risk
            </div>

            <div className="mt-4 space-y-4">
              {(selfHealing.predictive_risk ?? []).map(
                (risk, index) => {
                  const riskScore = Math.min(
                    riskMax,
                    Math.max(
                      0,
                      Number(
                        risk.risk_score ?? 0
                      )
                    )
                  );

                  return (
                    <div
                      key={`${risk.component}-${index}`}
                      className="
                        rounded-xl
                        border
                        border-slate-800
                        bg-slate-950/60
                        p-3
                        min-w-0
                      "
                    >
                      <div
                        className="
                          flex
                          items-center
                          justify-between
                          gap-3
                        "
                      >
                        <span
                          className="
                            min-w-0
                            text-sm
                            font-semibold
                            text-slate-100
                            truncate
                          "
                        >
                          {risk.component}
                        </span>

                        <span
                          className="
                            shrink-0
                            text-xs
                            font-bold
                            text-rose-300
                          "
                        >
                          {Math.round(riskScore)}%
                        </span>
                      </div>

                      <div
                        className="
                          mt-2
                          h-2
                          rounded-full
                          bg-slate-800
                          overflow-hidden
                        "
                      >
                        <div
                          className="
                            h-full
                            rounded-full
                            bg-gradient-to-r
                            from-rose-500
                            to-amber-400
                          "
                          style={{
                            width: `${riskScore}%`,
                          }}
                        />
                      </div>

                      <p
                        className="
                          mt-2
                          text-xs
                          text-slate-400
                        "
                      >
                        {risk.trigger}
                      </p>

                      <p
                        className="
                          mt-1
                          text-[11px]
                          text-slate-300
                          leading-relaxed
                        "
                      >
                        {risk.explanation}
                      </p>
                    </div>
                  );
                }
              )}

              {(selfHealing.predictive_risk ?? [])
                .length === 0 && (
                <div
                  className="
                    rounded-xl
                    border
                    border-slate-800
                    bg-slate-950/60
                    p-4
                    text-sm
                    text-slate-500
                  "
                >
                  No predictive risks detected.
                </div>
              )}
            </div>
          </div>

          {/* ================================================= */}
          {/* RISK PROPAGATION GRAPH                            */}
          {/* ================================================= */}

          <div
            className="
              rounded-2xl
              border
              border-slate-800
              bg-slate-900/80
              p-4
              sm:p-5
            "
          >
            <div
              className="
                flex
                items-center
                gap-2
                text-xs
                font-bold
                uppercase
                tracking-[0.12em]
                text-slate-300
              "
            >
              <GitBranch
                className="
                  w-4
                  h-4
                  text-emerald-400
                  shrink-0
                "
              />

              Risk propagation graph
            </div>

            <div className="mt-4 space-y-3">
              {(selfHealing.risk_graph ?? []).map(
                (edge, index) => (
                  <div
                    key={`${edge.source}-${edge.target}-${index}`}
                    className="
                      flex
                      items-center
                      gap-2
                      min-w-0
                      text-xs
                      text-slate-300
                    "
                  >
                    <span
                      className="
                        min-w-0
                        max-w-[40%]
                        font-mono
                        text-cyan-300
                        truncate
                      "
                    >
                      {edge.source}
                    </span>

                    <ArrowRight
                      className="
                        w-3.5
                        h-3.5
                        text-slate-500
                        shrink-0
                      "
                    />

                    <span
                      className="
                        min-w-0
                        max-w-[40%]
                        font-mono
                        text-violet-300
                        truncate
                      "
                    >
                      {edge.target}
                    </span>

                    <span
                      className={`
                        ml-auto
                        shrink-0
                        rounded-full
                        px-2
                        py-0.5
                        text-[10px]
                        font-bold
                        ${
                          edge.severity ===
                          "High"
                            ? "bg-rose-500/15 text-rose-300"
                            : edge.severity ===
                                "Medium"
                              ? "bg-amber-500/15 text-amber-300"
                              : "bg-slate-700 text-slate-300"
                        }
                      `}
                    >
                      {edge.severity}
                    </span>
                  </div>
                )
              )}

              {(selfHealing.risk_graph ?? [])
                .length === 0 && (
                <div
                  className="
                    rounded-xl
                    border
                    border-slate-800
                    bg-slate-950/60
                    p-4
                    text-sm
                    text-slate-500
                  "
                >
                  No propagation edges detected.
                </div>
              )}
            </div>
          </div>

          {/* ================================================= */}
          {/* REMEDIATION VELOCITY & DEVSECOPS SLA MATRIX      */}
          {/* ================================================= */}

          <div
            className="
              rounded-2xl
              border
              border-slate-800
              bg-slate-900/80
              p-4
              sm:p-5
              space-y-4
            "
          >
            <div
              className="
                flex
                items-center
                justify-between
                border-b
                border-slate-800/80
                pb-3
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-2
                  text-xs
                  font-bold
                  uppercase
                  tracking-[0.12em]
                  text-slate-300
                "
              >
                <Zap className="w-4 h-4 text-amber-400 shrink-0" />
                Remediation velocity & SLA
              </div>

              <span
                className="
                  px-2
                  py-0.5
                  rounded-md
                  text-[10px]
                  font-mono
                  font-bold
                  bg-emerald-500/10
                  text-emerald-400
                  border
                  border-emerald-500/20
                "
              >
                SLA: &lt;4h Critical
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 space-y-1">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <Timer className="w-3.5 h-3.5 text-blue-400" />
                  <span>Est. AutoFix MTTR</span>
                </div>
                <div className="text-base font-black text-slate-100">
                  ~{Math.max(5, (selfHealing.fixes_generated || 1) * 4)} mins
                </div>
                <div className="text-[10px] text-emerald-400 font-mono">
                  Autonomous sandbox ready
                </div>
              </div>

              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 space-y-1">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                  <span>Policy Enforced</span>
                </div>
                <div className="text-base font-black text-slate-100">
                  Zero-Trust
                </div>
                <div className="text-[10px] text-blue-400 font-mono">
                  AST Guardrails active
                </div>
              </div>
            </div>

            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <span className="text-slate-300 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  Secret & Token Hardening
                </span>
                <span className="text-[10px] font-mono text-emerald-400 font-bold">100% AST Scanned</span>
              </div>

              <div className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <span className="text-slate-300 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                  Vulnerability Patch SLA
                </span>
                <span className="text-[10px] font-mono text-cyan-400 font-bold">&lt; 24h Auto-PR</span>
              </div>

              <div className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40 border border-slate-800/60">
                <span className="text-slate-300 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                  CI/CD Quality Gate
                </span>
                <span className="text-[10px] font-mono text-purple-400 font-bold">Blocked on Criticals</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}