document.addEventListener("DOMContentLoaded", () => {
    const downloadReportButton = document.getElementById("download-report");

    downloadReportButton.addEventListener("click", async () => {
        if (!downloadReportButton.dataset.profile) {
            alert("No profile data available to generate a report.");
            return;
        }

        const profileData = JSON.parse(downloadReportButton.dataset.profile);
        try {
            const response = await fetch("/download_report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profileData)
            });

            if (!response.ok) throw new Error("Failed to generate report.");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "Personality_Profile_Report.pdf";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch (error) {
            alert("An error occurred while generating the report. Please try again.");
        }
    });
});
