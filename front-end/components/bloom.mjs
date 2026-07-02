import {apiService} from "../index.mjs";

/**
 * Create a bloom component
 * @param {string} template - The ID of the template to clone
 * @param {Object} bloom - The bloom data
 * @returns {DocumentFragment} - The bloom fragment of UI, for items in the Timeline
 * btw a bloom object is composed thus
 * {"id": Number,
 * "sender": username,
 * "content": "string from textarea",
 * "sent_timestamp": "datetime as ISO 8601 formatted string"}

 */
const createBloom = (template, bloom) => {
  if (!bloom) return;
  const bloomFrag = document.getElementById(template).content.cloneNode(true);
  const bloomParser = new DOMParser();

  const bloomArticle = bloomFrag.querySelector("[data-bloom]");
  const bloomUsername = bloomFrag.querySelector("[data-username]");
  const bloomTime = bloomFrag.querySelector("[data-time]");
  const bloomTimeLink = bloomFrag.querySelector("a:has(> [data-time])");
  const bloomContent = bloomFrag.querySelector("[data-content]");

  bloomArticle.setAttribute("data-bloom-id", bloom.id);
  bloomUsername.setAttribute("href", `/profile/${bloom.sender}`);
  bloomUsername.textContent = bloom.sender;
  bloomTime.textContent = _formatTimestamp(bloom.sent_timestamp);
  bloomTimeLink.setAttribute("href", `/bloom/${bloom.id}`);
  bloomContent.replaceChildren(
    ...bloomParser.parseFromString(_formatHashtags(bloom.content), "text/html")
      .body.childNodes
  );

  // Identify the new UI elements we added to the template
  const rebloomIndicator = bloomFrag.querySelector("[data-rebloom-indicator]");
  const rebloomerName = bloomFrag.querySelector("[data-rebloomer-name]");
  const rebloomButton = bloomFrag.querySelector("[data-action='rebloom']");
  const countElement = bloomFrag.querySelector("[data-rebloom-count]");

  // Conditional Logic: "If this data object represents a re-bloom..."
  if (bloom.rebloomer_username) {
    // Show the "Re-bloomed by" banner and set the name
    rebloomIndicator.style.display = "block"; 
    rebloomerName.textContent = bloom.rebloomer_username;

  }
  countElement.textContent = bloom.rebloom_count > 0 ? `(${bloom.rebloom_count})` : "";

  if (bloom.rebloomer_username || bloom.is_rebloomed_by_me) {
    rebloomButton.style.display = "none";
  }
  
  // Event Listener: "What happens when I click the button?"
  rebloomButton?.addEventListener("click", async () => {
    try {
      // We will need to create this function in api.mjs next!
      await apiService.rebloom(bloom.id); 
    } catch (error) {
      console.error("Re-bloom failed:", error);
    }
  });

  return bloomFrag;
};

function _formatHashtags(text) {
  if (!text) return text;
  return text.replace(
    /\B#[^#]+/g,
    (match) => `<a href="/hashtag/${match.slice(1)}">${match}</a>`
  );
}

function _formatTimestamp(timestamp) {
  if (!timestamp) return "";

  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffSeconds = Math.floor((now - date) / 1000);

    // Less than a minute
    if (diffSeconds < 60) {
      return `${diffSeconds}s`;
    }

    // Less than an hour
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) {
      return `${diffMinutes}m`;
    }

    // Less than a day
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) {
      return `${diffHours}h`;
    }

    // Less than a week
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) {
      return `${diffDays}d`;
    }

    // Format as month and day for older dates
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
    }).format(date);
  } catch (error) {
    console.error("Failed to format timestamp:", error);
    return "";
  }
}

export {createBloom};
