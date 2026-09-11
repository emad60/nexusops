import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { LoadingBlock } from "./components/ui";
import { ToastProvider } from "./components/toast";

// Code-split every page; the router owns chunk boundaries.
const LoginPage = lazy(() => import("./pages/LoginPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const ServerListPage = lazy(() => import("./pages/ServerListPage"));
const ServerDetailPage = lazy(() => import("./pages/ServerDetailPage"));
const ContainerListPage = lazy(() => import("./pages/ContainerListPage"));
const ContainerDetailPage = lazy(() => import("./pages/ContainerDetailPage"));
const DockerHostsPage = lazy(() => import("./pages/DockerHostsPage"));
const MonitorListPage = lazy(() => import("./pages/MonitorListPage"));
const MonitorDetailPage = lazy(() => import("./pages/MonitorDetailPage"));
const IncidentListPage = lazy(() => import("./pages/IncidentListPage"));
const IncidentDetailPage = lazy(() => import("./pages/IncidentDetailPage"));
const AlertsPage = lazy(() => import("./pages/AlertsPage"));
const DeploymentListPage = lazy(() => import("./pages/DeploymentListPage"));
const DeploymentDetailPage = lazy(() => import("./pages/DeploymentDetailPage"));
const ProjectListPage = lazy(() => import("./pages/ProjectListPage"));
const ProjectDetailPage = lazy(() => import("./pages/ProjectDetailPage"));
const EventsPage = lazy(() => import("./pages/EventsPage"));
const AuditLogPage = lazy(() => import("./pages/AuditLogPage"));
const SecretsPage = lazy(() => import("./pages/SecretsPage"));
const UsersPage = lazy(() => import("./pages/UsersPage"));
const RolesPage = lazy(() => import("./pages/RolesPage"));
const ApiKeysPage = lazy(() => import("./pages/ApiKeysPage"));
const SessionsPage = lazy(() => import("./pages/SessionsPage"));

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, initializing } = useAuth();
  const location = useLocation();
  if (initializing) return <LoadingBlock label="Starting NexusOps…" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

function LoginRoute() {
  const { user, initializing } = useAuth();
  if (initializing) return <LoadingBlock label="Starting NexusOps…" />;
  if (user) return <Navigate to="/" replace />;
  return <LoginPage />;
}

export function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Suspense fallback={<LoadingBlock />}>
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route path="/servers" element={<ServerListPage />} />
              <Route path="/servers/:serverId" element={<ServerDetailPage />} />
              <Route path="/containers" element={<ContainerListPage />} />
              <Route path="/containers/:containerId" element={<ContainerDetailPage />} />
              <Route path="/docker-hosts" element={<DockerHostsPage />} />
              <Route path="/monitors" element={<MonitorListPage />} />
              <Route path="/monitors/:monitorId" element={<MonitorDetailPage />} />
              <Route path="/incidents" element={<IncidentListPage />} />
              <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/deployments" element={<DeploymentListPage />} />
              <Route path="/deployments/:deploymentId" element={<DeploymentDetailPage />} />
              <Route path="/projects" element={<ProjectListPage />} />
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/audit-logs" element={<AuditLogPage />} />
              <Route path="/secrets" element={<SecretsPage />} />
              <Route path="/settings/users" element={<UsersPage />} />
              <Route path="/settings/roles" element={<RolesPage />} />
              <Route path="/settings/api-keys" element={<ApiKeysPage />} />
              <Route path="/settings/sessions" element={<SessionsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ToastProvider>
    </AuthProvider>
  );
}
