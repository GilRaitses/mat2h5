function [VelocityVec, speed] = compute_velocity_and_speed(xpos, ypos, times)
% COMPUTE_VELOCITY_AND_SPEED Compute velocity unit vectors and speed from positions
%
%   ORIGINAL MASON SCRIPT: Just_ReverseCrawl_Matlab.m
%   Location: scripts/2025-11-20/mason's scritps/
%
%   Original code (lines ~30-45):
%       for o = 1:(length(times)-1)
%           dx = xpos(o+1) - xpos(o);
%           dy = ypos(o+1) - ypos(o);
%           distance = sqrt(dx^2 + dy^2);
%           dt = times(o+1) - times(o);
%           if distance > 0 && dt > 0
%               VelocityVecx = dx / distance;
%               VelocityVecy = dy / distance;
%               speed = distance / dt;
%           end
%       end
%
%   [VelocityVec, speed] = compute_velocity_and_speed(xpos, ypos, times)
%
%   Mathematical Definition:
%       dx = xpos(i+1) - xpos(i)
%       dy = ypos(i+1) - ypos(i)
%       dt = times(i+1) - times(i)
%       distance = sqrt(dx^2 + dy^2)
%       VelocityVec = [dx/distance; dy/distance]  (normalized)
%       speed = distance / dt
%
%   Inputs:
%       xpos  - X positions, shape (1, N) or (N, 1)
%       ypos  - Y positions, shape (1, N) or (N, 1)
%       times - Time values, shape (1, N) or (N, 1)
%
%   Outputs:
%       VelocityVec - Normalized velocity vectors, shape (2, N-1)
%       speed       - Speed values, shape (1, N-1)
%
%   Reference: Mason Klein's reverse crawl detection method
%   Documentation: scripts/2025-11-24/mason_script_3_reverse_crawl.qmd
%   Python equivalent: engineer_data.compute_velocity_and_speed()

% Ensure row vectors
xpos = xpos(:)';
ypos = ypos(:)';
times = times(:)';

N = length(xpos);

% Compute displacements
dx = diff(xpos);  % (1, N-1)
dy = diff(ypos);  % (1, N-1)
dt = diff(times); % (1, N-1)

% Compute distance
distance = sqrt(dx.^2 + dy.^2);  % (1, N-1)

% Compute speed (distance / time)
speed = zeros(1, N-1);
valid_dt = dt > 0;
speed(valid_dt) = distance(valid_dt) ./ dt(valid_dt);

% Normalize velocity vectors
VelocityVec = zeros(2, N-1);
valid_dist = distance > 0;
VelocityVec(1, valid_dist) = dx(valid_dist) ./ distance(valid_dist);
VelocityVec(2, valid_dist) = dy(valid_dist) ./ distance(valid_dist);

end

%% Test Harness
function test_compute_velocity_and_speed()
    % Test case 1: Constant velocity along x-axis
    xpos = [0, 1, 2, 3, 4];
    ypos = [0, 0, 0, 0, 0];
    times = [0, 1, 2, 3, 4];
    
    [VelocityVec, speed] = compute_velocity_and_speed(xpos, ypos, times);
    
    expected_vel = [1, 1, 1, 1; 0, 0, 0, 0];
    expected_speed = [1, 1, 1, 1];
    
    assert(max(abs(VelocityVec(:) - expected_vel(:))) < 1e-10, 'Test 1 failed: velocity');
    assert(max(abs(speed - expected_speed)) < 1e-10, 'Test 1 failed: speed');
    fprintf('Test 1 passed: constant x-velocity\n');
    
    % Test case 2: Diagonal movement
    xpos = [0, 1, 2, 3];
    ypos = [0, 1, 2, 3];
    times = [0, 1, 2, 3];
    
    [VelocityVec, speed] = compute_velocity_and_speed(xpos, ypos, times);
    
    expected_vel = [1/sqrt(2), 1/sqrt(2), 1/sqrt(2); 1/sqrt(2), 1/sqrt(2), 1/sqrt(2)];
    expected_speed = [sqrt(2), sqrt(2), sqrt(2)];
    
    assert(max(abs(VelocityVec(:) - expected_vel(:))) < 1e-10, 'Test 2 failed: velocity');
    assert(max(abs(speed - expected_speed)) < 1e-10, 'Test 2 failed: speed');
    fprintf('Test 2 passed: diagonal movement\n');
    
    % Test case 3: Zero displacement (stationary)
    xpos = [1, 1, 1];
    ypos = [2, 2, 2];
    times = [0, 1, 2];
    
    [VelocityVec, speed] = compute_velocity_and_speed(xpos, ypos, times);
    
    expected_vel = [0, 0; 0, 0];
    expected_speed = [0, 0];
    
    assert(max(abs(VelocityVec(:) - expected_vel(:))) < 1e-10, 'Test 3 failed: velocity');
    assert(max(abs(speed - expected_speed)) < 1e-10, 'Test 3 failed: speed');
    fprintf('Test 3 passed: stationary\n');
    
    % Test case 4: Variable time steps
    xpos = [0, 2, 6];
    ypos = [0, 0, 0];
    times = [0, 1, 3];  % dt = [1, 2]
    
    [VelocityVec, speed] = compute_velocity_and_speed(xpos, ypos, times);
    
    expected_vel = [1, 1; 0, 0];
    expected_speed = [2, 2];  % distance/dt = [2/1, 4/2]
    
    assert(max(abs(VelocityVec(:) - expected_vel(:))) < 1e-10, 'Test 4 failed: velocity');
    assert(max(abs(speed - expected_speed)) < 1e-10, 'Test 4 failed: speed');
    fprintf('Test 4 passed: variable time steps\n');
    
    fprintf('\nAll tests passed for compute_velocity_and_speed!\n');
end

