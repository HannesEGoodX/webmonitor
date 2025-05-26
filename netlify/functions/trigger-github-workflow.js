// netlify/functions/trigger-github-workflow.js
const fetch = require("node-fetch");

exports.handler = async function (event, context) {
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      body: JSON.stringify({ message: "Method Not Allowed" }),
    };
  }

  const GITHUB_TOKEN = process.env.GITHUB_PAT;

  // --- IMPORTANT: REPLACE THESE PLACEHOLDERS ---
  const REPO_OWNER = "HannesEGoodX"; // Replace with your GitHub username (e.g., 'HannesEGoodX')
  const REPO_NAME = "webmonitor"; // This should be 'webmonitor' if that's your repo name
  const WORKFLOW_ID = "check_sites.yml";
  const REF_BRANCH = "main"; // Or 'master' if that's your default branch for GitHub Actions
  // --- END REPLACE ---

  if (!GITHUB_TOKEN || !REPO_OWNER) {
    console.error("Missing GITHUB_PAT or REPO_OWNER environment variable.");
    return {
      statusCode: 500,
      body: JSON.stringify({ message: "Server configuration error." }),
    };
  }

  try {
    const response = await fetch(
      `https://api.github.com/repos/<span class="math-inline">\{REPO\_OWNER\}/</span>{REPO_NAME}/actions/workflows/${WORKFLOW_ID}/dispatches`,
      {
        method: "POST",
        headers: {
          Accept: "application/vnd.github.v3+json",
          Authorization: `token ${GITHUB_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ref: REF_BRANCH,
        }),
      }
    );

    if (response.ok) {
      return {
        statusCode: 200,
        body: JSON.stringify({ message: "Workflow dispatched successfully!" }),
      };
    } else {
      const errorData = await response.json();
      console.error("GitHub API error:", errorData);
      return {
        statusCode: response.status,
        body: JSON.stringify({
          message:
            errorData.message || "Failed to dispatch workflow to GitHub.",
        }),
      };
    }
  } catch (error) {
    console.error("Netlify function error:", error);
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: `Internal server error: ${error.message}`,
      }),
    };
  }
};
