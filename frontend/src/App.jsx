import { Routes, Route } from 'react-router-dom';
import { TaskScreen } from './screens/TaskScreen';
import { MenuScreen } from './screens/MenuScreen';
import { CastleScreen } from './screens/CastleScreen';
import { BankScreen } from './screens/BankScreen';
import { ShopScreen } from './screens/ShopScreen';
import { ArtifactsScreen } from './screens/ArtifactsScreen';
import { AlchemyScreen } from './screens/AlchemyScreen';

function App() {
  const defaultUserId = "331113480";

  return (
    <Routes>
      <Route path="/" element={<MenuScreen userId={defaultUserId} />} />
      <Route path="/game/menu/:userId" element={<MenuScreen userId={defaultUserId} />} />
      <Route path="/game/task/:userId" element={<TaskScreen userId={defaultUserId} />} />
      <Route path="/game/castle/:userId" element={<CastleScreen userId={defaultUserId} />} />
      <Route path="/game/bank/:userId" element={<BankScreen userId={defaultUserId} />} />
      <Route path="/game/shop/:userId" element={<ShopScreen userId={defaultUserId} />} />
      <Route path="/game/shop/artifacts/:userId" element={<ArtifactsScreen userId={defaultUserId} />} />
      <Route path="/game/shop/alchemy/:userId" element={<AlchemyScreen userId={defaultUserId} />} />
    </Routes>
  );
}

export default App;