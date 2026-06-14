import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ScanList from "./pages/ScanList";
import NewScan from "./pages/NewScan";
import ScanDetail from "./pages/ScanDetail";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ScanList />} />
        <Route path="new" element={<NewScan />} />
        <Route path="scans/:id" element={<ScanDetail />} />
      </Route>
    </Routes>
  );
}

export default App;
