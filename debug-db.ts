import { getAgentById, getSkillsForAgent } from './lib/db/queries';

async function test() {
  const agentId = 'agnt_000VCRiAVlsz2Q9PHK9bXvQ4DZ';
  const workspaceId = 'wrk_000V7dMzXJLzP5mYgdf7FzjA3J';

  console.log('Testing getAgentById...');
  try {
    const agent = await getAgentById(agentId, workspaceId);
    console.log('Agent:', agent ? 'Found' : 'Not found');
  } catch (e) {
    console.error('Error in getAgentById:', e);
  }

  console.log('Testing getSkillsForAgent...');
  try {
    const skills = await getSkillsForAgent(agentId);
    console.log('Skills:', skills.length);
  } catch (e) {
    console.error('Error in getSkillsForAgent:', e);
  }
}

test();
