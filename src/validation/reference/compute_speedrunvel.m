function [SpeedRunVel, times_out] = compute_speedrunvel(shead, smid, xpos, ypos, times, lengthPerPixel)
% COMPUTE_SPEEDRUNVEL Compute signed velocity (SpeedRunVel) using dot product method
%
%   ORIGINAL MASON SCRIPT: Just_ReverseCrawl_Matlab.m
%   Location: scripts/2025-11-20/mason's scritps/
%
%   Original code (core computation):
%       HeadVec = shead - smid;
%       HeadUnitVec = HeadVec / norm(HeadVec);
%       VelocityVec = [dx/distance; dy/distance];
%       speed = distance / dt;
%       CosThetaFactor = dot(VelocityVec, HeadUnitVec);
%       SpeedRunVel = speed * CosThetaFactor;
%
%   KEY OUTPUT: SpeedRunVel is the central variable for reverse crawl detection
%   - SpeedRunVel > 0 means forward crawling
%   - SpeedRunVel < 0 means REVERSE CRAWL (backing up)
%
%   [SpeedRunVel, times_out] = compute_speedrunvel(shead, smid, xpos, ypos, times, lengthPerPixel)
%
%   Mathematical Definition:
%       HeadUnitVec = normalized(shead - smid)
%       VelocityVec = normalized displacement
%       SpeedRun = ||displacement|| / dt
%       CosThetaFactor = VelocityVec · HeadUnitVec
%       SpeedRunVel = SpeedRun × CosThetaFactor
%
%   Interpretation:
%       SpeedRunVel > 0  →  Forward movement (velocity aligned with head)
%       SpeedRunVel < 0  →  Reverse crawl (velocity opposite to head)
%       SpeedRunVel = 0  →  Stationary or perpendicular movement
%
%   Inputs:
%       shead          - Head positions, shape (2, N)
%       smid           - Midpoint positions, shape (2, N)
%       xpos           - X positions in pixels, shape (1, N) or (N, 1)
%       ypos           - Y positions in pixels, shape (1, N) or (N, 1)
%       times          - Time values, shape (1, N) or (N, 1)
%       lengthPerPixel - Conversion factor (cm/pixel), default 1.0
%
%   Outputs:
%       SpeedRunVel - Signed velocity array, shape (1, N-1)
%       times_out   - Time values for SpeedRunVel, shape (1, N-1)
%
%   Reference: Mason Klein's reverse crawl detection method
%   Documentation: scripts/2025-11-24/mason_scripts_documentation.qmd (Section 3)
%   Python equivalent: engineer_data.compute_speedrunvel()

if nargin < 6
    lengthPerPixel = 1.0;
end

% Ensure row vectors
xpos = xpos(:)';
ypos = ypos(:)';
times = times(:)';

% Convert positions to cm
xpos_cm = xpos * lengthPerPixel;
ypos_cm = ypos * lengthPerPixel;

% Compute heading unit vectors
HeadUnitVec = compute_heading_unit_vector(shead, smid);

% Compute velocity vectors and speed
[VelocityVec, speed] = compute_velocity_and_speed(xpos_cm, ypos_cm, times);

N = length(times) - 1;

% Compute dot product (CosThetaFactor)
% Use HeadUnitVec at each frame (truncate to match velocity length)
CosThetaFactor = sum(VelocityVec .* HeadUnitVec(:, 1:N), 1);

% SpeedRunVel = speed × cos(theta)
SpeedRunVel = speed .* CosThetaFactor;

% Times correspond to the first point of each interval
times_out = times(1:end-1);

end

%% Test Harness
function test_compute_speedrunvel()
    % Test case 1: Forward movement (heading and velocity aligned)
    % Head pointing right (+x), moving right
    shead = [2, 3, 4; 0, 0, 0];  % head at x=2,3,4
    smid = [1, 2, 3; 0, 0, 0];   % mid at x=1,2,3 (head - mid = [1,0])
    xpos = [0, 1, 2];            % moving right
    ypos = [0, 0, 0];
    times = [0, 1, 2];
    lengthPerPixel = 1.0;
    
    [SpeedRunVel, ~] = compute_speedrunvel(shead, smid, xpos, ypos, times, lengthPerPixel);
    
    % Heading = [1, 0], Velocity = [1, 0], dot product = 1, speed = 1
    % SpeedRunVel should be positive (forward)
    assert(all(SpeedRunVel > 0), 'Test 1 failed: forward movement should have positive SpeedRunVel');
    assert(max(abs(SpeedRunVel - 1)) < 1e-10, 'Test 1 failed: SpeedRunVel should be 1');
    fprintf('Test 1 passed: forward movement\n');
    
    % Test case 2: Reverse crawl (heading opposite to velocity)
    % Head pointing right (+x), moving left
    shead = [2, 3, 4; 0, 0, 0];  % head at x=2,3,4
    smid = [1, 2, 3; 0, 0, 0];   % mid at x=1,2,3 (head - mid = [1,0])
    xpos = [2, 1, 0];            % moving LEFT (reverse)
    ypos = [0, 0, 0];
    times = [0, 1, 2];
    
    [SpeedRunVel, ~] = compute_speedrunvel(shead, smid, xpos, ypos, times, lengthPerPixel);
    
    % Heading = [1, 0], Velocity = [-1, 0], dot product = -1, speed = 1
    % SpeedRunVel should be negative (reverse)
    assert(all(SpeedRunVel < 0), 'Test 2 failed: reverse movement should have negative SpeedRunVel');
    assert(max(abs(SpeedRunVel - (-1))) < 1e-10, 'Test 2 failed: SpeedRunVel should be -1');
    fprintf('Test 2 passed: reverse crawl\n');
    
    % Test case 3: Perpendicular movement (90 degrees)
    % Head pointing right (+x), moving up (+y)
    shead = [2, 3, 4; 0, 0, 0];  % head pointing +x
    smid = [1, 2, 3; 0, 0, 0];
    xpos = [0, 0, 0];            % not moving in x
    ypos = [0, 1, 2];            % moving up
    times = [0, 1, 2];
    
    [SpeedRunVel, ~] = compute_speedrunvel(shead, smid, xpos, ypos, times, lengthPerPixel);
    
    % Heading = [1, 0], Velocity = [0, 1], dot product = 0
    % SpeedRunVel should be 0
    assert(max(abs(SpeedRunVel)) < 1e-10, 'Test 3 failed: perpendicular should have zero SpeedRunVel');
    fprintf('Test 3 passed: perpendicular movement\n');
    
    % Test case 4: 45 degree angle
    shead = [1, 2, 3; 0, 0, 0];  % head pointing +x
    smid = [0, 1, 2; 0, 0, 0];
    xpos = [0, 1, 2];            % moving diagonally
    ypos = [0, 1, 2];
    times = [0, 1, 2];
    
    [SpeedRunVel, ~] = compute_speedrunvel(shead, smid, xpos, ypos, times, lengthPerPixel);
    
    % Heading = [1, 0], Velocity = [0.707, 0.707], dot product = 0.707
    % speed = sqrt(2), SpeedRunVel = sqrt(2) * 0.707 = 1
    expected = sqrt(2) * (1/sqrt(2));  % = 1
    assert(max(abs(SpeedRunVel - expected)) < 1e-10, 'Test 4 failed: 45 degree angle');
    fprintf('Test 4 passed: 45 degree angle\n');
    
    fprintf('\nAll tests passed for compute_speedrunvel!\n');
end

