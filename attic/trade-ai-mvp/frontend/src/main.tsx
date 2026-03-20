import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { router } from "./app/router";
import { AppUIProvider } from "./state/AppUIContext";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppUIProvider>
      <RouterProvider router={router} />
    </AppUIProvider>
  </React.StrictMode>
);
