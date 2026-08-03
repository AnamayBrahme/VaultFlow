import http from 'k6/http';
import { sleep, check } from 'k6';

// This configures a realistic traffic spike simulation
export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up to 10 concurrent users over 30s
    { duration: '1m', target: 10 },  // Stay at 10 users for 1 minute (steady traffic)
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
};

export default function () {
    const res = http.get('http://localhost:8443/health');
  
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(0.5); // Each user waits 500ms before hitting it again
}