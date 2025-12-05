function HeadUnitVec = compute_heading_unit_vector(shead, smid)
% COMPUTE_HEADING_UNIT_VECTOR Compute normalized heading vector from head and midpoint
%
%   ORIGINAL MASON SCRIPT: Just_ReverseCrawl_Matlab.m
%   Location: scripts/2025-11-20/mason's scritps/
%   
%   Original code (lines ~15-25):
%       HeadVec = shead - smid;
%       for k = 1:(size(HeadVec,2)-1)
%           norm_val = sqrt(HeadVec(1,k)^2 + HeadVec(2,k)^2);
%           if norm_val > 0
%               HeadUnitVec(:,k) = HeadVec(:,k) / norm_val;
%           end
%       end
%
%   HeadUnitVec = compute_heading_unit_vector(shead, smid)
%
%   Mathematical Definition:
%       HeadVec = shead - smid
%       HeadUnitVec = HeadVec / ||HeadVec||
%
%   Inputs:
%       shead - Head positions, shape (2, N) where rows are [x; y]
%       smid  - Midpoint positions, shape (2, N) where rows are [x; y]
%
%   Outputs:
%       HeadUnitVec - Normalized heading vectors, shape (2, N)
%
%   Reference: Mason Klein's reverse crawl detection method
%   Documentation: scripts/2025-11-24/mason_script_3_reverse_crawl.qmd
%   Python equivalent: engineer_data.compute_heading_unit_vector()
%
%   Example:
%       shead = [1, 2, 3; 1, 2, 3];  % 2x3
%       smid = [0, 1, 2; 0, 1, 2];   % 2x3
%       HeadUnitVec = compute_heading_unit_vector(shead, smid);
%       % Result: HeadUnitVec = [0.7071, 0.7071, 0.7071; 0.7071, 0.7071, 0.7071]

% Validate inputs
if size(shead, 1) ~= 2
    error('shead must have shape (2, N)');
end
if size(smid, 1) ~= 2
    error('smid must have shape (2, N)');
end
if size(shead, 2) ~= size(smid, 2)
    error('shead and smid must have same number of columns');
end

N = size(shead, 2);

% HeadVec = shead - smid
HeadVec = shead - smid;

% Compute norm for each time point
norms = sqrt(HeadVec(1, :).^2 + HeadVec(2, :).^2);

% Avoid division by zero
norms(norms == 0) = 1.0;

% Normalize: HeadUnitVec = HeadVec / ||HeadVec||
HeadUnitVec = HeadVec ./ norms;

end

%% Test Harness
function test_compute_heading_unit_vector()
    % Test case 1: Simple diagonal heading
    shead = [1, 2, 3; 1, 2, 3];
    smid = [0, 1, 2; 0, 1, 2];
    result = compute_heading_unit_vector(shead, smid);
    
    expected = [1/sqrt(2), 1/sqrt(2), 1/sqrt(2); 1/sqrt(2), 1/sqrt(2), 1/sqrt(2)];
    
    assert(max(abs(result(:) - expected(:))) < 1e-10, 'Test 1 failed: diagonal heading');
    fprintf('Test 1 passed: diagonal heading\n');
    
    % Test case 2: Horizontal heading (y=0)
    shead = [2, 4, 6; 0, 0, 0];
    smid = [0, 2, 4; 0, 0, 0];
    result = compute_heading_unit_vector(shead, smid);
    
    expected = [1, 1, 1; 0, 0, 0];
    
    assert(max(abs(result(:) - expected(:))) < 1e-10, 'Test 2 failed: horizontal heading');
    fprintf('Test 2 passed: horizontal heading\n');
    
    % Test case 3: Vertical heading (x=0)
    shead = [0, 0, 0; 3, 6, 9];
    smid = [0, 0, 0; 0, 3, 6];
    result = compute_heading_unit_vector(shead, smid);
    
    expected = [0, 0, 0; 1, 1, 1];
    
    assert(max(abs(result(:) - expected(:))) < 1e-10, 'Test 3 failed: vertical heading');
    fprintf('Test 3 passed: vertical heading\n');
    
    % Test case 4: Zero vector (shead == smid)
    shead = [1, 2, 3; 1, 2, 3];
    smid = [1, 2, 3; 1, 2, 3];
    result = compute_heading_unit_vector(shead, smid);
    
    % When norm is 0, we set it to 1, so result should be [0,0,0; 0,0,0]
    expected = [0, 0, 0; 0, 0, 0];
    
    assert(max(abs(result(:) - expected(:))) < 1e-10, 'Test 4 failed: zero vector');
    fprintf('Test 4 passed: zero vector handling\n');
    
    fprintf('\nAll tests passed for compute_heading_unit_vector!\n');
end

