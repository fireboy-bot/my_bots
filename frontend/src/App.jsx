import { Routes, Route, useParams, Navigate } from 'react-router-dom';
import { TaskScreen } from './screens/TaskScreen';
import { MenuScreen } from './screens/MenuScreen';
import { CastleScreen } from './screens/CastleScreen';
import { BankScreen } from './screens/BankScreen';
import { ShopScreen } from './screens/ShopScreen';
import { ArtifactsScreen } from './screens/ArtifactsScreen';
import { AlchemyScreen } from './screens/AlchemyScreen';

const DEFAULT_USER_ID = import.meta.env.VITE_DEFAULT_USER_ID || '331113480';

function useRouteUserId() {
  const { userId } = useParams();
  return userId || DEFAULT_USER_ID;
}

function MenuRoute() {
  return <MenuScreen userId={useRouteUserId()} />;
}

function TaskRoute() {
  return <TaskScreen userId={useRouteUserId()} />;
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

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={`/game/menu/${DEFAULT_USER_ID}`} replace />} />
      <Route path="/game/menu/:userId" element={<MenuRoute />} />
      <Route path="/game/task/:userId" element={<TaskRoute />} />
      <Route path="/game/castle/:userId" element={<CastleRoute />} />
      <Route path="/game/bank/:userId" element={<BankRoute />} />
      <Route path="/game/shop/:userId" element={<ShopRoute />} />
      <Route path="/game/shop/artifacts/:userId" element={<ArtifactsRoute />} />
      <Route path="/game/shop/alchemy/:userId" element={<AlchemyRoute />} />
    </Routes>
  );
}

export default App;
