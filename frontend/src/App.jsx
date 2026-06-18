import { Routes, Route, useParams, Navigate } from 'react-router-dom';
import { TaskScreen } from './screens/TaskScreen';
import { MenuScreen } from './screens/MenuScreen';
import { WorldsScreen } from './screens/WorldsScreen';
import { BossScreen } from './screens/BossScreen';
import { CastleScreen } from './screens/CastleScreen';
import { BankScreen } from './screens/BankScreen';
import { ShopScreen } from './screens/ShopScreen';
import { ArtifactsScreen } from './screens/ArtifactsScreen';
import { AlchemyScreen } from './screens/AlchemyScreen';
import { ProfileScreen } from './screens/ProfileScreen';
import { SecretRoomScreen } from './screens/SecretRoomScreen';
import { InventoryScreen } from './screens/InventoryScreen';
import { TrueLordScreen } from './screens/TrueLordScreen';

const DEFAULT_USER_ID = import.meta.env.VITE_DEFAULT_USER_ID || '331113480';

function useRouteUserId() {
  const { userId } = useParams();
  return userId || DEFAULT_USER_ID;
}

function MenuRoute() {
  return <MenuScreen userId={useRouteUserId()} />;
}

function WorldsRoute() {
  return <WorldsScreen userId={useRouteUserId()} />;
}

function BossRoute() {
  const { bossId } = useParams();
  const userId = useRouteUserId();
  if (bossId === 'true_lord') {
    return <TrueLordScreen userId={userId} />;
  }
  return <BossScreen userId={userId} bossId={bossId} />;
}

function TaskRoute() {
  const { worldId } = useParams();
  return <TaskScreen userId={useRouteUserId()} worldId={worldId} />;
}

function TaskLegacyRedirect() {
  const { userId } = useParams();
  return <Navigate to={`/game/worlds/${userId || DEFAULT_USER_ID}`} replace />;
}

function CastleRoute() {
  return <CastleScreen userId={useRouteUserId()} />;
}

function BankRoute() {
  return <BankScreen userId={useRouteUserId()} />;
}

function ShopRoute() {
  return <ShopScreen userId={useRouteUserId()} />;
}

function ArtifactsRoute() {
  return <ArtifactsScreen userId={useRouteUserId()} />;
}

function AlchemyRoute() {
  return <AlchemyScreen userId={useRouteUserId()} />;
}

function ProfileRoute() {
  return <ProfileScreen userId={useRouteUserId()} />;
}

function SecretRoomRoute() {
  return <SecretRoomScreen userId={useRouteUserId()} />;
}

function InventoryRoute() {
  return <InventoryScreen userId={useRouteUserId()} />;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={`/game/menu/${DEFAULT_USER_ID}`} replace />} />
      <Route path="/game/menu/:userId" element={<MenuRoute />} />
      <Route path="/game/worlds/:userId" element={<WorldsRoute />} />
      <Route path="/game/boss/:userId/:bossId" element={<BossRoute />} />
      <Route path="/game/task/:userId/:worldId" element={<TaskRoute />} />
      <Route path="/game/task/:userId" element={<TaskLegacyRedirect />} />
      <Route path="/game/castle/:userId" element={<CastleRoute />} />
      <Route path="/game/bank/:userId" element={<BankRoute />} />
      <Route path="/game/shop/:userId" element={<ShopRoute />} />
      <Route path="/game/shop/artifacts/:userId" element={<ArtifactsRoute />} />
      <Route path="/game/shop/alchemy/:userId" element={<AlchemyRoute />} />
      <Route path="/game/profile/:userId" element={<ProfileRoute />} />
      <Route path="/game/secret-room/:userId" element={<SecretRoomRoute />} />
      <Route path="/game/inventory/:userId" element={<InventoryRoute />} />
    </Routes>
  );
}

export default App;
