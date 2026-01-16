let videoData = [];
const API_URL = "http://127.0.0.1:8000/analyze_video"; 

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("videoInput");
    const video = document.getElementById("videoPlayer");
    const canvas = document.getElementById("videoCanvas");
    const ctx = canvas.getContext("2d");
    const btn = document.getElementById("analyzeBtn");

    // Load Video Preview
    input.addEventListener("change", () => {
        if (input.files[0]) {
            video.src = URL.createObjectURL(input.files[0]);
            video.style.display = "block";
        }
    });

    // DRAWING LOOP (Matches your Screenshots)
    video.addEventListener("timeupdate", () => {
        if (!video.videoWidth) return;
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const t = video.currentTime;
        const d = videoData.find(x => Math.abs(x.time - t) < 0.3);

        if (d) {
            // 1. DRAW BOUNDING BOX (Cyan/Teal)
            const box = (d.tools && d.tools.length > 0) ? d.tools[0].bbox : d.crit_region;
            if (box) {
                const [x1, y1, x2, y2] = box;
                ctx.strokeStyle = "#22d3ee"; // Cyan
                ctx.lineWidth = 4;
                ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
            }

            // 2. TEXT OVERLAYS
            let yPos = 50;
            ctx.font = "bold 28px Arial";
            ctx.shadowColor="black";
            ctx.shadowBlur=4;
            
            // A. VISIBILITY
            let visColor = d.visibility === "POOR" ? "red" : (d.visibility === "MODERATE" ? "#fb923c" : "#4ade80");
            ctx.fillStyle = visColor;
            
            let visText = `Visibility: ${d.visibility}`;
            if (d.vis_reason) visText += ` (${d.vis_reason})`;
            visText += ` | ${d.vis_score}%`;
            
            ctx.fillText(visText, 30, yPos);
            yPos += 40;

            // B. CONTEXTUAL RISK
            let riskColor = (d.risk_level === "CRITICAL" || d.risk_level === "HIGH") ? "red" : "#fb923c";
            ctx.fillStyle = riskColor;
            ctx.fillText(`Contextual Risk: ${d.risk_level}`, 30, yPos);
            yPos += 40;

            // C. PROCEDURE
            ctx.fillStyle = "white";
            ctx.fillText(`Procedure: LAPAROSCOPY`, 30, yPos);
            yPos += 40;

            // D. FLAGS (e.g. "??? TOOL_PROXIMITY")
            if (d.safety_flags && d.safety_flags.length > 0) {
                ctx.fillStyle = "#e2e8f0"; // Light Gray
                d.safety_flags.forEach(flag => {
                    ctx.fillText(`??? ${flag}`, 30, yPos);
                    yPos += 40;
                });
            }
            ctx.shadowBlur=0;
        }
    });

    // ANALYZE BUTTON
    if (btn) btn.addEventListener("click", async () => {
        const status = document.getElementById("status");
        const reportBox = document.getElementById("textReport");

        if (!input.files[0]) return alert("Please select a video file first!");

        const fd = new FormData();
        fd.append("file", input.files[0]);

        status.innerText = "⏳ Uploading & Analyzing... (Check Terminal for Progress)";
        if (reportBox) reportBox.style.display = "none";

        try {
            const res = await fetch(API_URL, { method: "POST", body: fd });
            
            // Handle Errors Gracefully
            if (!res.ok) {
                const errJson = await res.json();
                throw new Error(errJson.error || res.statusText);
            }

            const data = await res.json();
            videoData = data.events; 
            status.innerText = "✅ Analysis Complete!";

            // GENERATE REPORT (Matches your Dark Theme Screenshot)
            if (reportBox) {
                const r = data.report;
                const duration = `${Math.floor(r.duration_sec / 60)} min ${r.duration_sec % 60} sec`;
                
                reportBox.style.display = "block";
                reportBox.innerHTML = `
                    <h2 style="border-bottom: 1px solid #fff; padding-bottom: 10px;">SURGICAL SAFETY REPORT</h2>
                    <p><strong>Procedure Duration:</strong> ${duration}</p>

                    <h3 style="color: #cbd5e1;">VISIBILITY ANALYSIS:</h3>
                    <ul>
                        <li>Good visibility: ${r.vis_breakdown.good}%</li>
                        <li>Moderate visibility: ${r.vis_breakdown.moderate}%</li>
                        <li>Poor visibility: ${r.vis_breakdown.poor}%</li>
                    </ul>

                    <h3 style="color: #cbd5e1;">SAFETY EVENTS:</h3>
                    <ul>
                        <li>Tool collision risks: ${r.event_counts.TOOL_PROXIMITY}</li>
                        <li>Critical region alerts: ${r.event_counts.CRITICAL_REGION}</li>
                        <li>Fast tool movements: ${r.event_counts.HIGH_TOOL_SPEED}</li>
                    </ul>
                    <p><strong>Potential Safety Events Detected:</strong> ${r.total_risk_events}</p>
                    <p><strong>Triggered under:</strong></p>
                    <ul>
                        ${r.reduced_visibility_risk > 0 ? '<li>Reduced visibility</li>' : ''}
                        ${r.event_counts.TOOL_PROXIMITY > 0 ? '<li>High tool proximity</li>' : ''}
                        ${r.event_counts.HIGH_TOOL_SPEED > 0 ? '<li>Fast tool movements</li>' : ''}
                    </ul>

                    <h3>OVERALL RISK LEVEL: <span style="color: ${r.overall_risk === 'SAFE' ? '#4ade80' : (r.overall_risk === 'MODERATE' ? 'orange' : 'white')}">${r.overall_risk}</span></h3>

                    <h3 style="color: #cbd5e1;">KEY INSIGHT:</h3>
                    <p style="border-left: 3px solid #facc15; padding-left: 10px; color: #facc15;">
                        ${r.reduced_visibility_risk > r.total_risk_events/2 
                          ? "Most risk events occurred under reduced visibility." 
                          : "Risk events were distributed across conditions."}
                    </p>
                `;
            }
            video.play();
        } catch (e) {
            console.error(e);
            status.innerText = "❌ Error: " + e.message;
        }
    });
});