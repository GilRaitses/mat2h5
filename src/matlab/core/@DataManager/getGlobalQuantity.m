function gq_data = getGlobalQuantity(obj, gq_index)
    % getGlobalQuantity - Get a single global quantity field
    % Uses PROVEN pattern from loadExperiment.m line 65-67
    %
    % Inputs:
    %   gq_index - Index into globalQuantity array
    %
    % Returns:
    %   gq_data - Struct with fieldname, yData, xData, units, etc.
    
    if isempty(obj.eset) || isempty(obj.eset.expt)
        gq_data = [];
        return;
    end
    
    expt = obj.eset.expt(1);
    
    % PROVEN PATTERN from loadExperiment.m
    gq = expt.globalQuantity(gq_index);
    
    gq_data = struct();
    gq_data.fieldname = gq.fieldname;
    gq_data.yData = gq.yData;
    
    % Optional fields
    if isprop(gq, 'xData') && ~isempty(gq.xData)
        gq_data.xData = gq.xData;
    end
    if isprop(gq, 'units') && ~isempty(gq.units)
        gq_data.units = gq.units;
    end
    if isprop(gq, 'derivtype') && ~isempty(gq.derivtype)
        gq_data.derivtype = gq.derivtype;
    end
end

