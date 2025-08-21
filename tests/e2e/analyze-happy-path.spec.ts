import { test, expect } from '@playwright/test';

test('happy path: analyze resume flow', async ({ page }) => {
  // Navigate to the analyze page
  await page.goto('/');
  
  // Wait for the page to load
  await expect(page.getByText('Resume Analysis')).toBeVisible();
  
  // Fill in job title
  await page.getByPlaceholder('e.g., Software Engineer').fill('Frontend Developer');
  
  // Fill in job description
  const jdText = `
Frontend Developer - React & TypeScript
We are seeking a skilled Frontend Developer to join our team.

Responsibilities:
- Build responsive web applications using React and TypeScript
- Implement modern UI/UX designs with attention to detail  
- Collaborate with backend teams on API integration
- Write unit tests and maintain code quality
- Optimize application performance

Requirements:
- 3+ years experience with React and JavaScript
- Strong knowledge of TypeScript
- Experience with modern CSS frameworks
- Understanding of RESTful APIs
- Git version control experience

Preferred:
- Next.js framework experience
- Testing with Jest or Playwright
- AWS cloud services knowledge
- Agile development methodologies
`;
  
  await page.getByPlaceholder('Paste the job description here...').fill(jdText.trim());
  
  // Fill in resume content
  const resumeText = `
John Smith
john.smith@email.com | (555) 123-4567

SUMMARY
Frontend developer with 4 years of experience building responsive web applications using React, TypeScript, and modern JavaScript frameworks. Passionate about creating intuitive user experiences and writing clean, maintainable code.

SKILLS
React, TypeScript, JavaScript, HTML5, CSS3, Redux, Next.js, Node.js, Git, Jest, AWS, RESTful APIs, Agile

EXPERIENCE

Frontend Developer  Jan 2022 – Present
TechCorp Inc., San Francisco, CA
• Developed and maintained React applications serving 50,000+ daily active users
• Implemented TypeScript migration reducing runtime errors by 40%
• Built responsive components using CSS modules and styled-components
• Collaborated with UX team to implement pixel-perfect designs
• Integrated RESTful APIs and managed state with Redux
• Wrote comprehensive unit tests achieving 85% code coverage

Junior Frontend Developer  Mar 2020 – Dec 2021  
StartupXYZ, Austin, TX
• Built customer-facing web applications using React and JavaScript
• Participated in Agile development processes and daily standups
• Optimized application performance improving load times by 25%
• Worked closely with backend developers on API design

EDUCATION
University of Texas • Bachelor of Science in Computer Science • 2020
`;
  
  await page.getByPlaceholder('Paste your resume content here...').fill(resumeText.trim());
  
  // Click analyze button
  await page.getByRole('button', { name: 'Analyze Resume' }).click();
  
  // Wait for analysis to complete (with generous timeout for API calls)
  await expect(page.getByText('Analysis Results')).toBeVisible({ timeout: 15000 });
  
  // Check that we got a score
  const scoreElement = page.locator('[class*="badge"]').filter({ hasText: /\/100$/ });
  await expect(scoreElement).toBeVisible();
  
  // Check sections are displayed  
  await expect(page.getByText('Skills Coverage:')).toBeVisible();
  await expect(page.getByText('Preferred Skills:')).toBeVisible();
  await expect(page.getByText('Domain Terms:')).toBeVisible();
  
  // Check skills analysis table is present
  await expect(page.getByText('Skills Analysis')).toBeVisible();
  
  // Check that matched and missing skills are shown
  const skillsTable = page.locator('table');
  await expect(skillsTable).toBeVisible();
  
  // Check job requirements analysis
  await expect(page.getByText('Job Requirements Analysis')).toBeVisible();
  await expect(page.getByText('Required Skills')).toBeVisible();
  await expect(page.getByText('Key Responsibilities')).toBeVisible();
  
  // Check resume experience section with edit buttons
  await expect(page.getByText('Resume Experience (Edit to Improve)')).toBeVisible();
  await expect(page.getByText('Frontend Developer at TechCorp Inc.')).toBeVisible();
  
  // Test rewrite functionality
  const firstEditButton = page.locator('button').filter({ has: page.locator('svg') }).first();
  await firstEditButton.hover();
  await expect(firstEditButton).toBeVisible();
  await firstEditButton.click();
  
  // Check rewrite drawer opens
  await expect(page.getByText('Rewrite Bullet Point')).toBeVisible();
  await expect(page.getByText('AI will optimize this bullet point')).toBeVisible();
  
  // Check original text is populated
  const originalTextarea = page.getByLabel('Original Text');
  await expect(originalTextarea).toHaveValue(/Developed and maintained React applications/);
  
  // Check target keywords are shown
  await expect(page.getByText('Target Keywords')).toBeVisible();
  
  // Close the drawer
  await page.keyboard.press('Escape');
  await expect(page.getByText('Rewrite Bullet Point')).not.toBeVisible();
});