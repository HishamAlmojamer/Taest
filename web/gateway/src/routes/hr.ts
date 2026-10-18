import { Router } from 'express';
import { createBackendProxy } from '../services/pythonProxy';

const router = Router();
const proxy = createBackendProxy();

router.all('*', proxy);

export default router;
