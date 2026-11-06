[
  {
    "repo_url": "https://github.com/example/sample_todo.git",
    "bug_description": "When updating a TODO item, the backend does not verify if the ID in the URL matches the ID in the request body, potentially allowing an item's ID to be overwritten."
  },
  {
    "repo_url": "https://github.com/example/sample_todo.git",
    "bug_description": "Because the backend uses an in-memory list for storage, all created TODO items are permanently lost whenever the FastAPI server restarts."
  },
  {
    "repo_url": "https://github.com/example/sample_food_delivery.git",
    "bug_description": "Adding the same food item multiple times to the cart creates duplicate individual entries in the UI instead of grouping them together and incrementing the quantity."
  },
  {
    "repo_url": "https://github.com/example/sample_food_delivery.git",
    "bug_description": "The checkout process succeeds even when the cart is empty if the user double-clicks the checkout button rapidly."
  }
]
