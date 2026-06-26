# Project Log: PurpleForest - Re-bloom Feature Implementation

## 1. Feature Overview
Implemented a "Re-bloom" (sharing) system that allows users to redistribute existing posts to their own followers. This required a synchronized update across the database, backend services, and frontend UI components.

---

## 2. Structural Changes

### A. Database Layer (The Memory)
*   **New Table:** Created a `reblooms` table.
*   **Data Integrity Logic:** Used `BIGINT` for the `bloom_id` column to match the 64-bit timestamp-based IDs used in the legacy `blooms` table. This prevented `NumericValueOutOfRange` errors discovered during testing.
*   **Automation:** Set the `rebloom_timestamp` to `DEFAULT CURRENT_TIMESTAMP` to automate chronological sorting without extra backend logic.

### B. Backend Layer (The Brain)
*   **Model Update:** Expanded the `Bloom` class blueprint to include `rebloomer_username` and `rebloom_count` as optional attributes.
*   **Data Aggregation:** 
    *   Developed a `get_reblooms_for_user` function using SQL **JOINs** to link shared IDs back to original post content and author metadata.
    *   Updated the `home_timeline` endpoint to fetch both original blooms and re-blooms.
*   **Validation & Security:** Protected the new `POST /rebloom/<id>` endpoint with `@jwt_required` to ensure only authenticated users can share content.
*   **Counting Logic:** Implemented a **LEFT JOIN** and **GROUP BY** in the SQL queries to calculate how many times a post has been shared without hiding posts with zero shares.

### C. Frontend Layer (The Face)
*   **Template Logic:** Modified `index.html` to include a conditional "Re-bloom Indicator" banner and a "Re-bloom" action button.
*   **Component Logic (`bloom.mjs`):** 
    *   Implemented **Conditional Rendering** to show the attribution banner only when `rebloomer_username` exists in the data.
    *   Added **State Control** to hide the "Re-bloom" button on posts that are already re-blooms, preventing "re-blooming a re-bloom."
*   **Service Layer (`api.mjs`):** Added a `rebloom` method to handle the network request and trigger an automatic UI refresh upon success.

---

## 3. Logical Challenges & Resolutions
*   **The Sorting Puzzle:** To ensure re-blooms appeared at the top of the feed despite the original post being old, I used SQL aliasing (`AS sent_timestamp`) to make the re-bloom's time compatible with the existing sorting algorithm.
*   **The Import Conflict:** Resolved a `ReferenceError` by correctly importing the `apiService` into the `bloom.mjs` component, bridging the gap between the UI and the API layer.
*   **The Unpacking Error:** Fixed a `ValueError` by ensuring the number of variables in the Python loop matched the number of columns returned by the updated SQL `SELECT` statement.

---

## 4. Verification & Testing
*   **Database Verification:** Confirmed row insertion in DBeaver via manual SQL refresh.
*   **Social Logic Test:** Created a new user (`Tester`), followed the `sample` account, and verified that `sample`'s re-blooms correctly appeared in `Tester`'s timeline.
*   **UI Integrity:** Confirmed the re-bloom count increases dynamically on the original post when a share action is performed.

