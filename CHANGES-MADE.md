# Project Log: PurpleForest - Un-follow Feature Implementation

## 1. Feature Overview
Developed the "Un-follow" functionality to allow users to stop seeing blooms from specific accounts. This required building a "Reverse Path" that mirrors the "Follow" logic but executes a deletion in the database.

---

## 2. Structural Changes

### A. Database Layer (The Memory)
*   **Logic:** Implemented the removal of data using the SQL `DELETE` command. 
*   **Precision:** Used a `WHERE` clause targeting both the `follower` and the `followee` IDs. 
*   **The "Why":** This ensures the operation only removes the specific relationship between two users without accidentally deleting all follows for a single user.

### B. Backend Layer (The Brain)
*   **Data Logic (`data/follows.py`):** 
    *   Created the `unfollow` function.
    *   Used **parameterized queries** with a dictionary to safely pass user IDs to the database driver.
*   **API Endpoint (`endpoints.py`):** 
    *   Developed the `do_unfollow` controller.
    *   **Contract Matching:** Designed the function to accept `target_username` directly from the URL path to stay consistent with the existing Frontend API service.
    *   **Security:** Applied the `@jwt_required` middleware to ensure only the authenticated account owner can modify their following list.
*   **Routing (`main.py`):** Registered the new `/unfollow/<target_username>` route and imported the necessary logic from the endpoints module.

### C. Frontend Layer (The Face)
*   **Visibility Logic (`profile.mjs`):** 
    *   Modified the `createProfile` component to prevent the button from being hidden when a user is already followed.
    *   **The Toggle:** Implemented an `if/else` block to dynamically change the button text between "Follow" and "Un-follow" based on the `is_following` state.
*   **Event Handling (`profile.mjs`):** 
    *   Upgraded the `handleFollow` function into a **"Smart Switch."**
    *   **The Logic:** The handler now inspects the current text of the button. If it says "Un-follow," it calls the `unfollowUser` API; otherwise, it calls the standard `followUser` API.

---

## 4. Verification & Testing
*   **Action Verification:** Confirmed that clicking "Follow" changes the UI to "Un-follow" and vice-versa.
*   **Data Integrity:** Used **DBeaver** to verify that the corresponding row in the `follows` table is physically removed upon clicking "Un-follow."
*   **Social Feed Test:** Verified that un-following a user immediately stops their posts from appearing in the Home timeline upon the next refresh.

