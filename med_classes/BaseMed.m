classdef BaseMed < dynamicprops
    properties
        % Meta-data: Should be present for every med protocol
        File
        Start_Date
        End_Date
        Subject
        Experiment
        Group
        Box
        Start_Time
        End_Time
        MSN

        % Properties for syncing to posix time
        sync_med
        sync_posix
        sync_success = false % This flag get switched to indicate successful syncing to posix

    end
    properties (Abstract)
        name_conversion % Pairing of med name to friendly name
        time_arrays % Which arrays should get converted to posix
    end

    methods
        function obj = BaseMed(parsed_med)
            arguments
                parsed_med (1,1) struct
            end
            obj.set_parameters_from_parsed_med(parsed_med);

        end

        function set_parameters_from_parsed_med(obj, parsed_med)
            arguments
                obj
                parsed_med (1,1) struct
            end

            % Loop through all of the parsed med file fields
            med_fields = fieldnames(parsed_med);
            nm_conv = obj.name_conversion; %Make a copy of name_conversion for keeping track of which fields still need set
            for i=1:length(med_fields)
                f = med_fields{i};

                % Use property name from name_conversion if possible
                if isfield(obj.name_conversion, f)
                    new_name = obj.name_conversion.(f);
                    obj.set_prop(new_name, parsed_med.(f));
                    obj.set_alias(f, new_name)
                    nm_conv = rmfield(nm_conv, f);
                else
                    obj.set_prop(f, parsed_med.(f));
                end
            end

            if ~isempty(fieldnames(nm_conv))
                warning("The following fields from name_conversion were not present in the parsed med file. Setting to empty array. \n %s \n", formattedDisplayText(nm_conv))
                fields = fieldnames(nm_conv);
                for i=1:length(fields)
                    f=fields{i};
                    new_name = nm_conv.(f);
                    obj.set_prop(new_name, []);
                    obj.set_alias(f, new_name)
                end
            end


        end

        function set_prop(obj, prop_name, val)
            % Dynamically add property if needed
            if ~isprop(obj, prop_name)
                addprop(obj, prop_name);
            end
            % Set the property value
            obj.(prop_name) = val;
        end

        function set_alias(obj, alias, original)
            % Dynamically add property if needed
            if isprop(obj, alias)
                p = obj.findprop(alias);
            else
                p = addprop(obj, alias);
            end

            % Set to hidden and define getter/setter to alias
            p.Hidden = true;
            p.GetMethod = @(x) x.(original);
            p.SetMethod = @(x, val) setPrimary(x, original, val);
        end

        function convert2posix(obj)
            plot(obj.sync_med, obj.sync_posix)
            p_fit = polyfit(obj.sync_med,obj.sync_posix,1);

            for i=1:numel(obj.time_arrays)
                field = obj.time_arrays{i};
                if ~isprop(obj, field)
                    error("Cannot convert %s to posix time as no such " + ...
                        "property exists for this class. Is %s missing" + ...
                        " from the name_conversion struct?", field,field)
                end
                obj.(field) = polyval(p_fit, field);
            end
            obj.sync_success = true;
        end


        function gpio = get_pi_gpio(obj, gpio_path)
            gpio = readtable(gpio_path);
            dt = datetime(gpio.Time, 'InputFormat', 'yyyyMMdd_HHmmss_SSSSSS', ...
                'TimeZone', 'America/Indianapolis');
            gpio.posix = posixtime(dt);
        end
    end
end

% Helper function for setting alias (cannot be an anonymous function if it modifies the object)
function setPrimary(obj, prop_name, val)
obj.(prop_name) = val;
end